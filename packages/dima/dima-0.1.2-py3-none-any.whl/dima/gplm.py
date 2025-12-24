# src/dima/gplm.py
from __future__ import annotations

from typing import Any, Dict, Literal, Optional, Tuple, Union, overload

import numpy as np
import scipy.linalg as la

from .ann import ANNBackend, make_ann
from .utils import fps_indices, median_eps_from_knn_d2, sqdist_ab

InducingMode = Literal["random_subset", "fps", "kmeans_medoids", "given"]


def _kmeans2_safe(Z: np.ndarray, m: int, seed: int = 0) -> np.ndarray:
    """
    KMeans centers with a safe fallback.
    Uses scipy.cluster.vq.kmeans2 if available; otherwise samples points.
    """
    Z = np.asarray(Z)
    m = int(min(max(1, m), Z.shape[0]))
    try:
        from scipy.cluster.vq import kmeans2  # type: ignore
        C, _ = kmeans2(Z.astype(np.float64, copy=False), m, minit="points", seed=seed)
        return C.astype(Z.dtype, copy=False)
    except Exception:
        rng = np.random.default_rng(seed)
        idx = rng.choice(Z.shape[0], size=m, replace=False)
        return Z[idx]


class GPLM:
    """
    Inducing-point / Nyström GP (kernel ridge) decoder on latents.

    Decoder:
      z = R_ax ∈ R^d
      f(z) = R_aX ∈ R^D

      Choose inducing Z_mx (m << N), typically subset/medoids of training latents.

      Weights (RBF affinity in latent):
        w_am = exp(-beta * ||z_a - Z_m||^2 / eps)

      Prediction:
        R_aX = w_a• @ M_mX + mean_X

    Jacobian (optional):
      J_aXx = ∂ R_aX / ∂ z_ax  (shape: (a, D, d))
      Metric (pullback):
        g_axx = J^T J  (shape: (a, d, d))

    Notes:
      - Supports BOTH ascii kwargs and unicode kwargs
        (β, ε, κ_eps, σ2, pred_κ, ε_use_kth, ε_mul).
      - If whiten_latent=True, distances are computed in whitened latent space, but
        Jacobians are returned w.r.t. the *unwhitened* input latents R_ax via chain rule.
    """

    def __init__(
        self,
        R_ix: np.ndarray,
        R_iX: np.ndarray,
        *,
        # ASCII names (preferred)
        beta: float = 1.0,

        # eps estimation
        eps: Optional[float] = None,
        k_eps: int = 256,
        eps_use_kth: bool = True,
        eps_mul: float = 1.0,

        # regularization
        sigma2: float = 1e-5,
        jitter: float = 1e-8,

        # inducing
        m: int = 1024,
        inducing: InducingMode = "kmeans_medoids",
        Z_mx: Optional[np.ndarray] = None,
        seed: int = 0,

        # preprocess
        center_X: bool = True,
        whiten_latent: bool = False,
        dtype: Any = np.float32,

        # compute/memory
        fit_block: int = 8192,

        # inference
        pred_k: Optional[int] = None,
        ann_backend: ANNBackend = "auto",
        ann_params: Optional[Dict[str, Any]] = None,
        n_jobs: int = -1,

        # accept unicode kwargs (β, ε, κ_eps, σ2, pred_κ, ...)
        **kwargs: Any,
    ):
        # ---- map unicode kwargs -> ascii ----
        if "β" in kwargs:
            beta = kwargs.pop("β")
        if "ε" in kwargs:
            eps = kwargs.pop("ε")
        if "κ_eps" in kwargs:
            k_eps = kwargs.pop("κ_eps")
        if "ε_use_kth" in kwargs:
            eps_use_kth = kwargs.pop("ε_use_kth")
        if "ε_mul" in kwargs:
            eps_mul = kwargs.pop("ε_mul")
        if "σ2" in kwargs:
            sigma2 = kwargs.pop("σ2")
        if "pred_κ" in kwargs:
            pred_k = kwargs.pop("pred_κ")

        if kwargs:
            raise TypeError(f"Unexpected kwargs: {sorted(kwargs.keys())}")

        # ---- store params (provide both spellings) ----
        self.beta = float(beta)
        self.β = self.beta

        self.sigma2 = float(sigma2)
        self.σ2 = self.sigma2

        self.jitter = float(jitter)
        self.seed = int(seed)
        self.dtype = dtype
        self.fit_block = int(fit_block)

        # ---- validate / cast ----
        R_ix = np.ascontiguousarray(np.asarray(R_ix).astype(self.dtype, copy=False))
        R_iX = np.ascontiguousarray(np.asarray(R_iX).astype(self.dtype, copy=False))
        if R_ix.ndim != 2 or R_iX.ndim != 2 or R_ix.shape[0] != R_iX.shape[0]:
            raise ValueError("R_ix must be (N,d) and R_iX must be (N,D) with same N.")

        self.R_ix = R_ix
        self.R_iX = R_iX
        self.N, self.d_lat = R_ix.shape
        _, self.D = R_iX.shape

        # ---- center output ----
        if center_X:
            self.mean_X = R_iX.mean(axis=0).astype(np.float64)
            Y = (R_iX.astype(np.float64) - self.mean_X[None, :])
        else:
            self.mean_X = np.zeros((self.D,), dtype=np.float64)
            Y = R_iX.astype(np.float64)

        # ---- latent whitening (optional) ----
        Ztrain = R_ix.astype(np.float64)
        if whiten_latent:
            self.lat_mean_x = Ztrain.mean(axis=0)
            self.lat_std_x = np.maximum(Ztrain.std(axis=0), 1e-12)
            Ztrain_w = (Ztrain - self.lat_mean_x) / self.lat_std_x
        else:
            self.lat_mean_x = np.zeros((self.d_lat,), dtype=np.float64)
            self.lat_std_x = np.ones((self.d_lat,), dtype=np.float64)
            Ztrain_w = Ztrain

        self.R_ix_w = Ztrain_w  # (N,d) float64

        # ---- ANN on training latents (for eps + medoids snapping) ----
        self.ann_train, self.ann_backend = make_ann(ann_backend, ann_params=ann_params, n_jobs=n_jobs)
        self.ann_train.build(self.R_ix_w.astype(self.dtype, copy=False))

        # ---- eps via kNN distances on latents ----
        if eps is None:
            k_eps = int(min(max(8, int(k_eps)), self.N - 1))
            j_iK1, D2_iK1 = self.ann_train.search(self.R_ix_w.astype(self.dtype, copy=False), k_eps + 1)

            i = np.arange(self.N)[:, None]
            is_self = (j_iK1 == i)
            if np.any(is_self):
                D2_iK = np.empty((self.N, k_eps), dtype=np.float64)
                for ii in range(self.N):
                    keep = (j_iK1[ii] != ii)
                    D2_iK[ii] = D2_iK1[ii][keep][:k_eps]
            else:
                D2_iK = D2_iK1[:, :k_eps].astype(np.float64, copy=False)

            eps_hat = median_eps_from_knn_d2(D2_iK, use_kth=bool(eps_use_kth))
        else:
            eps_hat = float(eps)

        eps_hat *= float(eps_mul)
        if eps_hat <= 0:
            raise ValueError("eps must be > 0.")
        self.eps = float(eps_hat)
        self.ε = self.eps

        # ---- choose inducing points (in whitened latent space) ----
        rng = np.random.default_rng(self.seed)
        m = int(min(max(1, int(m)), self.N))

        if Z_mx is not None:
            Zm = np.asarray(Z_mx, dtype=np.float64)
            if Zm.ndim != 2 or Zm.shape[1] != self.d_lat:
                raise ValueError("Z_mx must be (m, d_lat).")
            Zm_w = (Zm - self.lat_mean_x) / self.lat_std_x
        else:
            if inducing == "random_subset":
                idx = rng.choice(self.N, size=m, replace=False)
                Zm_w = self.R_ix_w[idx]
            elif inducing == "fps":
                idx = fps_indices(self.R_ix_w, m=m, seed=self.seed)
                Zm_w = self.R_ix_w[idx]
            elif inducing == "kmeans_medoids":
                C = _kmeans2_safe(self.R_ix_w, m, seed=self.seed).astype(np.float64, copy=False)
                j_cm, _ = self.ann_train.search(C.astype(self.dtype, copy=False), 1)
                idx = j_cm.reshape(-1).astype(np.int64)

                idx_u = np.unique(idx)
                if idx_u.size < m:
                    needed = m - idx_u.size
                    pool = np.setdiff1d(np.arange(self.N), idx_u, assume_unique=False)
                    extra = rng.choice(pool, size=needed, replace=False) if pool.size >= needed else rng.choice(self.N, size=needed, replace=True)
                    idx = np.concatenate([idx_u, extra])
                else:
                    idx = idx_u[:m]
                Zm_w = self.R_ix_w[idx]
            elif inducing == "given":
                raise ValueError("Provide Z_mx when inducing='given'.")
            else:
                raise ValueError(f"Unknown inducing mode: {inducing!r}")

        self.Z_mx_w = np.ascontiguousarray(Zm_w.astype(np.float64, copy=False))
        self.m = int(self.Z_mx_w.shape[0])

        # also store raw inducing points (unwhitened) for convenience/serialization
        self.Z_mx = (self.Z_mx_w * self.lat_std_x[None, :]) + self.lat_mean_x[None, :]

        # ---- ANN on inducing points for fast prediction ----
        self.ann_Z, _ = make_ann(ann_backend, ann_params=ann_params, n_jobs=n_jobs)
        self.ann_Z.build(self.Z_mx_w.astype(self.dtype, copy=False))

        # pred_k
        if pred_k is None:
            self.pred_k = None
        else:
            self.pred_k = int(min(max(1, int(pred_k)), self.m))
        self.pred_κ = self.pred_k  # unicode alias

        # ---- W_mm ----
        D2_mm = sqdist_ab(self.Z_mx_w, self.Z_mx_w)
        W_mm = np.exp(-self.beta * (D2_mm.astype(np.float64) / self.eps))
        W_mm.flat[:: self.m + 1] += self.jitter
        self.W_mm = W_mm  # (m,m)

        # ---- accumulate G=C^T C and B=C^T Y ----
        G_mm = np.zeros((self.m, self.m), dtype=np.float64)
        B_mX = np.zeros((self.m, self.D), dtype=np.float64)

        bs = int(self.fit_block)
        for i0 in range(0, self.N, bs):
            i1 = min(self.N, i0 + bs)
            Zi = self.R_ix_w[i0:i1]  # (b,d) float64
            D2_im = sqdist_ab(Zi, self.Z_mx_w)
            C_im = np.exp(-self.beta * (D2_im.astype(np.float64) / self.eps))
            G_mm += C_im.T @ C_im
            B_mX += C_im.T @ Y[i0:i1]

        A_mm = G_mm + self.sigma2 * W_mm
        A_mm.flat[:: self.m + 1] += self.jitter

        cF = la.cho_factor(A_mm, lower=True, check_finite=False)
        self.M_mX = la.cho_solve(cF, B_mX, check_finite=False)  # (m,D), float64

        # cached constant used in d/dz of RBF
        self._rbf_grad_scale = (-2.0 * self.beta / self.eps)  # scalar

    # -------------------------
    # Public decode interface
    # -------------------------
    def __call__(
        self,
        R_ax: Union[np.ndarray, list],
        *,
        batch_size: Optional[int] = None,
        jacobian: bool = False,
        metric: bool = False,
    ):
        """
        Decode latents to ambient.

        Returns:
          - if jacobian=False and metric=False: Y (a,D)
          - if jacobian=True, metric=False: (Y, J) where J is (a,D,d)
          - if jacobian=False, metric=True: (Y, g) where g is (a,d,d)
          - if jacobian=True, metric=True: (Y, J, g)
        """
        R_ax = np.asarray(R_ax)
        single = (R_ax.ndim == 1)
        if single:
            R_ax = R_ax[None, :]
        R_ax = np.ascontiguousarray(R_ax.astype(self.dtype, copy=False))

        if batch_size is None:
            out = self._decode(R_ax, jacobian=jacobian, metric=metric)
        else:
            bs = int(batch_size)
            Ys = []
            Js = [] if jacobian else None
            Gs = [] if metric else None
            for s in range(0, R_ax.shape[0], bs):
                chunk = self._decode(R_ax[s:s + bs], jacobian=jacobian, metric=metric)
                if (not jacobian) and (not metric):
                    Ys.append(chunk)
                elif jacobian and (not metric):
                    Yc, Jc = chunk
                    Ys.append(Yc); Js.append(Jc)  # type: ignore[arg-type]
                elif (not jacobian) and metric:
                    Yc, gc = chunk
                    Ys.append(Yc); Gs.append(gc)  # type: ignore[arg-type]
                else:
                    Yc, Jc, gc = chunk
                    Ys.append(Yc); Js.append(Jc); Gs.append(gc)  # type: ignore[arg-type]

            Y = np.vstack(Ys)
            if (not jacobian) and (not metric):
                out = Y
            elif jacobian and (not metric):
                out = (Y, np.vstack(Js))  # type: ignore[arg-type]
            elif (not jacobian) and metric:
                out = (Y, np.vstack(Gs))  # type: ignore[arg-type]
            else:
                out = (Y, np.vstack(Js), np.vstack(Gs))  # type: ignore[arg-type]

        # unwrap single
        if single:
            if (not jacobian) and (not metric):
                return out[0]  # type: ignore[index]
            if jacobian and (not metric):
                Y, J = out  # type: ignore[misc]
                return Y[0], J[0]
            if (not jacobian) and metric:
                Y, g = out  # type: ignore[misc]
                return Y[0], g[0]
            Y, J, g = out  # type: ignore[misc]
            return Y[0], J[0], g[0]

        return out

    def _decode(
        self,
        R_ax: np.ndarray,
        *,
        jacobian: bool,
        metric: bool,
    ):
        """
        Internal decode for a batch (a,d).

        Jacobian is w.r.t. *unwhitened* input R_ax (chain rule applied if whiten_latent=True).
        """
        Za = R_ax.astype(np.float64)                            # (a,d)
        Za_w = (Za - self.lat_mean_x) / self.lat_std_x          # (a,d)

        # We'll need this for chain rule in gradients:
        inv_std = (1.0 / self.lat_std_x).astype(np.float64)     # (d,)

        if self.pred_k is None or self.pred_k == self.m:
            # full inducing
            D2_am = sqdist_ab(Za_w, self.Z_mx_w)                                # (a,m)
            W_am = np.exp(-self.beta * (D2_am.astype(np.float64) / self.eps))   # (a,m)
            Y = W_am @ self.M_mX                                                # (a,D)

            if not (jacobian or metric):
                return Y + self.mean_X[None, :]

            # diff in whitened latent space: (a,m,d)
            diff_amd = Za_w[:, None, :] - self.Z_mx_w[None, :, :]

            # dW/dZa_w: (a,m,d)
            dW_amd = (self._rbf_grad_scale * W_am[:, :, None]) * diff_amd

            # chain to unwhitened: dW/dZa = dW/dZa_w * dZa_w/dZa = * (1/std)
            dW_amd *= inv_std[None, None, :]

            if jacobian:
                # J_{a,D,d} = Σ_m dW_{a,m,d} * M_{m,D}
                J_aDd = np.einsum("amd,mD->aDd", dW_amd, self.M_mX, optimize=True)
                if metric:
                    g_add = np.einsum("aDd,aDe->ade", J_aDd, J_aDd, optimize=True)
                    return (Y + self.mean_X[None, :], J_aDd, g_add)
                return (Y + self.mean_X[None, :], J_aDd)

            # metric-only
            # Build J implicitly then g; for simplicity we materialize J here.
            J_aDd = np.einsum("amd,mD->aDd", dW_amd, self.M_mX, optimize=True)
            g_add = np.einsum("aDd,aDe->ade", J_aDd, J_aDd, optimize=True)
            return (Y + self.mean_X[None, :], g_add)

        # sparse inducing neighbors for speed
        j_aK, D2_aK = self.ann_Z.search(Za_w.astype(self.dtype, copy=False), self.pred_k)  # (a,k), (a,k)
        W_aK = np.exp(-self.beta * (D2_aK.astype(np.float64) / self.eps))                  # (a,k)
        M_aKD = self.M_mX[j_aK]                                                            # (a,k,D)
        Y = np.sum(W_aK[:, :, None] * M_aKD, axis=1)                                       # (a,D)

        if not (jacobian or metric):
            return Y + self.mean_X[None, :]

        Zsel_aKd = self.Z_mx_w[j_aK]               # (a,k,d) in whitened latent
        diff_aKd = Za_w[:, None, :] - Zsel_aKd     # (a,k,d)

        dW_aKd = (self._rbf_grad_scale * W_aK[:, :, None]) * diff_aKd
        dW_aKd *= inv_std[None, None, :]

        if jacobian:
            # J_{a,D,d} = Σ_k dW_{a,k,d} * M_{a,k,D}
            J_aDd = np.einsum("akd,akD->aDd", dW_aKd, M_aKD, optimize=True)
            if metric:
                g_add = np.einsum("aDd,aDe->ade", J_aDd, J_aDd, optimize=True)
                return (Y + self.mean_X[None, :], J_aDd, g_add)
            return (Y + self.mean_X[None, :], J_aDd)

        # metric-only
        J_aDd = np.einsum("akd,akD->aDd", dW_aKd, M_aKD, optimize=True)
        g_add = np.einsum("aDd,aDe->ade", J_aDd, J_aDd, optimize=True)
        return (Y + self.mean_X[None, :], g_add)


__all__ = ["GPLM", "InducingMode"]
