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

from dataclasses import dataclass

def sqdist_ab(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """
    Pairwise squared Euclidean distances between rows:
      A: (a,d), B: (b,d)  ->  D2: (a,b)
    """
    A = np.asarray(A, dtype=np.float64)
    B = np.asarray(B, dtype=np.float64)
    AA = np.sum(A * A, axis=1, keepdims=True)          # (a,1)
    BB = np.sum(B * B, axis=1, keepdims=True).T        # (1,b)
    D2 = AA + BB - 2.0 * (A @ B.T)
    return np.maximum(D2, 0.0)


class GPLM:
    """
    GPLM decoder with optional ANN sparse inducing prediction, plus a geodesic "flow" integrator.

    Required stored arrays/params:
      - Z_mx_w : (m,d) inducing points in *whitened latent coords*
      - M_mX   : (m,D) inducing outputs
      - mean_X : (D,) output mean added to decode
      - lat_mean_x : (d,) latent mean (for whitening)
      - lat_std_x  : (d,) latent std  (for whitening)
      - beta, eps  : RBF hyperparams used exactly as in your _decode
      - pred_k : if not None and < m, use ANN sparse neighbors
      - ann_Z : object with method: search(query: (a,d), k:int) -> (idx: (a,k), D2: (a,k))

    Notes:
      - __call__ and _decode are kept behavior-identical to your pasted version.
      - flow() integrates geodesics of the pullback metric g = J^T J induced by this decoder.
    """

    def __init__(
        self,
        *,
        Z_mx_w: np.ndarray,
        M_mX: np.ndarray,
        mean_X: np.ndarray,
        lat_mean_x: Optional[np.ndarray] = None,
        lat_std_x: Optional[np.ndarray] = None,
        beta: float = 1.0,
        eps: float = 1.0,
        pred_k: Optional[int] = None,
        ann_Z=None,
        dtype=np.float32 ):
        self.dtype = dtype

        self.Z_mx_w = np.asarray(Z_mx_w, dtype=np.float64)  # (m,d) whitened inducing
        self.M_mX = np.asarray(M_mX, dtype=np.float64)      # (m,D)
        self.mean_X = np.asarray(mean_X, dtype=np.float64)  # (D,)

        self.m = int(self.M_mX.shape[0])
        self.d = int(self.Z_mx_w.shape[1])
        self.D = int(self.M_mX.shape[1])

        if lat_mean_x is None:
            lat_mean_x = np.zeros(self.d, dtype=np.float64)
        if lat_std_x is None:
            lat_std_x = np.ones(self.d, dtype=np.float64)

        self.lat_mean_x = np.asarray(lat_mean_x, dtype=np.float64)  # (d,)
        self.lat_std_x = np.asarray(lat_std_x, dtype=np.float64)    # (d,)

        self.beta = float(beta)
        self.eps = float(eps)

        self.pred_k = pred_k
        self.ann_Z = ann_Z

        # matches your code: scale used in dW = scale * W * diff
        self._rbf_grad_scale = float(-2.0 * self.beta / self.eps)

        if self.pred_k is not None:
            if int(self.pred_k) <= 0:
                raise ValueError("pred_k must be positive or None.")
            if self.ann_Z is None:
                raise ValueError("ann_Z must be provided when pred_k is not None.")

    # -------------------------
    # Your original public API
    # -------------------------
    def __call__(
        self,
        R_ax: Union[np.ndarray, list],
        *,
        batch_size: Optional[int] = None,
        jacobian: bool = False,
        metric: bool = False ):
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
        metric: bool ):
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

    # -------------------------
    # NEW: Geodesic flow (analytic Christoffels) with generalized velocity-Verlet
    # -------------------------
    def flow(
        self,
        R_ax: Union[np.ndarray, list],
        v0_ax: Union[np.ndarray, list],
        *,
        dt: float = 0.05,
        reg: float = 1e-8,
        keep_speed: bool = True,
        ) -> Tuple[np.ndarray, np.ndarray]:
        """
        One generalized velocity-Verlet / leapfrog step for the geodesic ODE:
          r_dot = v
          v_dot^x = - Γ^x_{yz}(r) v^y v^z

        Returns:
          Q_ax : next latent positions (a,d)
          v_ax : next latent velocities (a,d)

        Use in a loop:
          Q, v = R0, v0
          for _ in range(T):
              Q, v = gplm.flow(Q, v, dt=...)
        """
        Z = np.asarray(R_ax, dtype=np.float64)
        v = np.asarray(v0_ax, dtype=np.float64)

        single = (Z.ndim == 1)
        if single:
            Z = Z[None, :]
        if v.ndim == 1:
            v = v[None, :]

        if Z.shape != v.shape:
            raise ValueError(f"R_ax and v0_ax must have same shape; got {Z.shape} vs {v.shape}")

        # a_n = a(z_n, v_n)
        a0, g0 = self._geodesic_accel_analytic(Z, v, reg=reg)

        # v_{n+1/2}
        v_half = v + 0.5 * float(dt) * a0

        # z_{n+1}
        Q = Z + float(dt) * v_half

        # a_{n+1} = a(z_{n+1}, v_{n+1/2})
        a1, g1 = self._geodesic_accel_analytic(Q, v_half, reg=reg)

        # v_{n+1}
        v_new = v_half + 0.5 * float(dt) * a1

        # Optional: keep Riemannian speed sqrt(v^T g v) constant per sample
        if keep_speed:
            s0 = np.sqrt(np.maximum(np.einsum("ai,aij,aj->a", v, g0, v, optimize=True), 1e-16))
            s1 = np.sqrt(np.maximum(np.einsum("ai,aij,aj->a", v_new, g1, v_new, optimize=True), 1e-16))
            v_new = v_new * (s0 / s1)[:, None]

        if single:
            return Q[0], v_new[0]
        return Q, v_new

    def _geodesic_accel_analytic(
        self,
        R_ax: np.ndarray,
        v_ax: np.ndarray,
        *,
        reg: float,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute acceleration a_ax = -Γ^x_{yz}(r) v^y v^z using analytic Christoffels,
        and return (a_ax, g_aij).

        Shapes:
          R_ax: (a,d)
          v_ax: (a,d)
          a_ax: (a,d)
          g:    (a,d,d)
        """
        Z = np.asarray(R_ax, dtype=np.float64)
        v = np.asarray(v_ax, dtype=np.float64)
        a, d = Z.shape
        if v.shape != (a, d):
            raise ValueError(f"v_ax must have shape {(a, d)}, got {v.shape}")

        # Precompute whitening + chain rule
        Za_w = (Z - self.lat_mean_x) / self.lat_std_x         # (a,d)
        inv_std = (1.0 / self.lat_std_x).astype(np.float64)   # (d,)
        alpha = float(self._rbf_grad_scale)

        I = np.eye(d, dtype=np.float64)

        if self.pred_k is None or self.pred_k == self.m:
            # ----- full inducing -----
            diff_amd = Za_w[:, None, :] - self.Z_mx_w[None, :, :]         # (a,m,d)
            D2_am = np.sum(diff_amd * diff_amd, axis=2)                   # (a,m)
            k_am = np.exp(-self.beta * (D2_am / self.eps))                # (a,m)

            # ∂_y k_am = alpha * k_am * D_amy * (1/σ_y)
            dk_amd = (alpha * k_am[:, :, None]) * diff_amd                # (a,m,d) (still whitened diffs)
            dk_amd *= inv_std[None, None, :]                              # chain to unwhitened

            # J_{aXy} = Σ_m (∂_y k_am) M_{mX}
            J_aXy = np.einsum("amd,mX->aXd", dk_amd, self.M_mX, optimize=True)  # (a,D,d)

            # metric g_{ayz} = J_{aXy} J_{aXz}
            g_ayz = np.einsum("aXd,aXe->ade", J_aXy, J_aXy, optimize=True)      # (a,d,d)
            g_ayz = 0.5 * (g_ayz + np.swapaxes(g_ayz, 1, 2))                    # symmetrize

            g_inv = np.linalg.inv(g_ayz + reg * I[None, :, :])                  # (a,d,d)

            # dg[a, w, y, z] = ∂_w g_{yz}
            dg_awyz = np.zeros((a, d, d, d), dtype=np.float64)

            # For each derivative index w, build Hessian slice H_{X w y} (as (a,D,y))
            for w in range(d):
                diff_w_am = diff_amd[:, :, w]  # (a,m)

                # ∂_{w y} k = k * [ alpha^2 * D_w * D_y + alpha * δ_{wy} ] * (1/σ_w)(1/σ_y)
                d2k_amy = k_am[:, :, None] * (
                    (alpha * alpha) * diff_w_am[:, :, None] * diff_amd
                    + alpha * I[w][None, None, :]
                )  # (a,m,d) in whitened diffs
                d2k_amy *= (inv_std[w] * inv_std[None])[None, None, :]  # chain factors (1/σ_w)(1/σ_y)

                # H_{aXy} for this w: H_{aXwy} = Σ_m (∂_{w y} k_am) M_{mX}
                H_w_aXy = np.einsum("amy,mX->aXd", d2k_amy, self.M_mX, optimize=True)  # (a,D,d)

                # ∂_w g_{yz} = H_{X w y} J_{X z} + J_{X y} H_{X w z}
                dg_w = (
                    np.einsum("aXd,aXe->ade", H_w_aXy, J_aXy, optimize=True)
                    + np.einsum("aXd,aXe->ade", J_aXy, H_w_aXy, optimize=True)
                )  # (a,d,d)
                dg_awyz[:, w, :, :] = dg_w

        else:
            # ----- sparse ANN inducing neighbors -----
            j_aK, D2_aK = self.ann_Z.search(Za_w.astype(self.dtype, copy=False), int(self.pred_k))  # (a,k),(a,k)
            k_aK = np.exp(-self.beta * (D2_aK.astype(np.float64) / self.eps))                        # (a,k)

            Zsel_aKd = self.Z_mx_w[j_aK]                    # (a,k,d)
            diff_aKd = Za_w[:, None, :] - Zsel_aKd          # (a,k,d)
            M_aKX = self.M_mX[j_aK]                         # (a,k,D)

            dk_aKd = (alpha * k_aK[:, :, None]) * diff_aKd
            dk_aKd *= inv_std[None, None, :]

            # J_{aXy} = Σ_k (∂_y k_aK) M_{aKX}
            J_aXy = np.einsum("akd,akX->aXd", dk_aKd, M_aKX, optimize=True)  # (a,D,d)

            g_ayz = np.einsum("aXd,aXe->ade", J_aXy, J_aXy, optimize=True)   # (a,d,d)
            g_ayz = 0.5 * (g_ayz + np.swapaxes(g_ayz, 1, 2))

            g_inv = np.linalg.inv(g_ayz + reg * I[None, :, :])               # (a,d,d)

            dg_awyz = np.zeros((a, d, d, d), dtype=np.float64)

            for w in range(d):
                diff_w_aK = diff_aKd[:, :, w]  # (a,k)

                d2k_aKy = k_aK[:, :, None] * (
                    (alpha * alpha) * diff_w_aK[:, :, None] * diff_aKd
                    + alpha * I[w][None, None, :]
                )  # (a,k,d)
                d2k_aKy *= (inv_std[w] * inv_std[None])[None, None, :]

                H_w_aXy = np.einsum("akd,akX->aXd", d2k_aKy, M_aKX, optimize=True)  # (a,D,d)

                dg_w = (
                    np.einsum("aXd,aXe->ade", H_w_aXy, J_aXy, optimize=True)
                    + np.einsum("aXd,aXe->ade", J_aXy, H_w_aXy, optimize=True)
                )
                dg_awyz[:, w, :, :] = dg_w

        # Christoffels:
        # A[y,z,w] = ∂_y g_{zw} + ∂_z g_{yw} - ∂_w g_{yz}
        # with dg stored as dg[w,y,z] = ∂_w g_{yz}
        A_ayzw = (
            dg_awyz
            + dg_awyz.transpose(0, 2, 1, 3)
            - dg_awyz.transpose(0, 2, 3, 1)
        )  # (a,y,z,w)

        # Gamma[a,x,y,z] = 1/2 * g_inv[a,x,w] * A[a,y,z,w]
        Gamma_axyz = 0.5 * np.einsum("axw,ayzw->axyz", g_inv, A_ayzw, optimize=True)

        # acceleration: a^x = - Γ^x_{yz} v^y v^z
        a_ax = -np.einsum("axyz,ay,az->ax", Gamma_axyz, v, v, optimize=True)

        return a_ax, g_ayz


__all__ = ["GPLM", "InducingMode"]
