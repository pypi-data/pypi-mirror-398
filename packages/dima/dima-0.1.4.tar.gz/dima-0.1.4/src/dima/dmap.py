# src/dima/dmap.py
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple, Union

import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import eigsh, LinearOperator, lobpcg

from .ann import ANNBackend, make_ann
from .utils import median_eps_from_knn_d2


def k_ideal(d: int, N: int) -> int:
    """
    Heuristic for kNN graph size in diffusion maps.
    Stable default: grows slowly with N and linearly with d.
    """
    d = int(max(1, d))
    N = int(max(2, N))
    k = int(np.ceil(2.0 * d * np.log2(N)))
    return int(min(max(8, k), N - 1))


def _sqdist_ab(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """
    Squared Euclidean distances between rows:
      A: (a,d), B: (b,d) -> D2: (a,b)
    """
    A = np.asarray(A, dtype=np.float64)
    B = np.asarray(B, dtype=np.float64)
    A2 = np.sum(A * A, axis=1, keepdims=True)
    B2 = np.sum(B * B, axis=1, keepdims=True).T
    G = A @ B.T
    return np.maximum(A2 + B2 - 2.0 * G, 0.0)


class DMAP:
    """
    Diffusion Maps encoder with Nyström out-of-sample extension.

    Notation (arrays named by indices):

      R_iX: reference ambient data
      K_ij: kernel on graph edges (sparse CSR)
      q_i = Σ_j K_ij
      qα_i = (q_i)^α
      Kα_ij = K_ij / (qα_i qα_j)
      d_i = Σ_j Kα_ij
      A_ij = Kα_ij / sqrt(d_i d_j)  (symmetric)

      eigsh(A) -> λ_x, u_ix
      ψ_ix = u_ix / sqrt(d_i)
      R_ix = (λ_x)^t ψ_ix

    Nyström OOS for novel ambient R_aX:
      K_ai = exp(-β * D2_ai / ε)
      q_a = Σ_i K_ai,  qα_a = (q_a)^α
      Kα_ai = K_ai / (qα_a qα_i)
      d_a = Σ_i Kα_ai
      P_ai = Kα_ai / d_a
      R_ax = Σ_i P_ai * (R_ix / λ_x)

    Extras (from your latest version):
      - refine_dense: warm-start with sparse kNN eigsh, then refine with streaming-matvec LOBPCG
      - stream_block: tile size for dense kernel streaming
      - lobpcg_maxiter / lobpcg_tol: refinement controls
      - use_symmetry: exploit K symmetry in dense matvec (roughly ~2x fewer tiles)
    """

    def __init__(
        self,
        R_iX: np.ndarray,
        *,
        # preferred ASCII names
        d: int = 6,
        k: Optional[int] = None,
        beta: float = 1.0,
        alpha: float = 0.0,
        t: float = 1.0,
        drop_trivial: bool = True,
        seed: int = 0,
        ann_backend: ANNBackend = "auto",
        ann_params: Optional[Dict[str, Any]] = None,
        n_jobs: int = -1,
        eps: Optional[float] = None,
        eps_use_kth: bool = True,
        eps_mul: float = 1.0,
        sym: str = "max",
        nL: Optional[int] = None,
        L_iX: Optional[np.ndarray] = None,
        dtype: Any = np.float32,
        # dense refinement (O(N^2) compute, streaming memory)
        refine_dense: bool = False,
        stream_block: int = 4096,
        lobpcg_maxiter: int = 3,
        lobpcg_tol: float = 1e-6,
        use_symmetry: bool = True,
        # allow unicode kwargs (β, α, ε, ε_mul, ε_use_kth, ...)
        **kwargs: Any,
    ):
        # ---- map unicode kwargs -> ascii ----
        if "β" in kwargs:
            beta = kwargs.pop("β")
        if "α" in kwargs:
            alpha = kwargs.pop("α")
        if "ε" in kwargs:
            eps = kwargs.pop("ε")
        if "ε_use_kth" in kwargs:
            eps_use_kth = kwargs.pop("ε_use_kth")
        if "ε_mul" in kwargs:
            eps_mul = kwargs.pop("ε_mul")
        if "sym" in kwargs:
            sym = kwargs.pop("sym")
        if kwargs:
            raise TypeError(f"Unexpected kwargs: {sorted(kwargs.keys())}")

        self.d = int(d)
        self.k = int(k_ideal(self.d, int(np.asarray(R_iX).shape[0])) if k is None else int(k))

        self.beta = float(beta)
        self.alpha = float(alpha)
        self.t = float(t)
        self.drop_trivial = bool(drop_trivial)
        self.seed = int(seed)
        self.sym = str(sym)
        self.dtype = dtype

        # unicode aliases (so older code + your packer can find them)
        self.β = self.beta
        self.α = self.alpha

        self.refine_dense = bool(refine_dense)
        self.stream_block = int(stream_block)
        self.lobpcg_maxiter = int(lobpcg_maxiter)
        self.lobpcg_tol = float(lobpcg_tol)
        self.use_symmetry = bool(use_symmetry)

        rng = np.random.default_rng(self.seed)

        # ---- choose reference set (landmarks optional) ----
        R_iX = np.asarray(R_iX)
        if L_iX is not None:
            R_iXref = np.asarray(L_iX)
        elif nL is not None:
            nL = int(nL)
            if nL <= 0 or nL > R_iX.shape[0]:
                raise ValueError("nL must be in [1, N].")
            sel = rng.choice(R_iX.shape[0], size=nL, replace=False)
            R_iXref = R_iX[sel]
        else:
            R_iXref = R_iX

        R_iXref = np.ascontiguousarray(R_iXref.astype(self.dtype, copy=False))
        Nref = int(R_iXref.shape[0])
        if self.k >= Nref:
            raise ValueError(f"k={self.k} must be < Nref={Nref}.")

        # ---- ANN on reference ----
        self.ann, self.ann_backend = make_ann(ann_backend, ann_params=ann_params, n_jobs=n_jobs)
        self.ann.build(R_iXref)
        self.R_iX = R_iXref  # store reference set

        # ---- kNN on reference (ask k+1 to try to include self) ----
        j_iK1, D2_iK1 = self.ann.search(R_iXref, self.k + 1)  # (Nref,k+1)

        # drop self neighbor if present
        i = np.arange(Nref)[:, None]
        is_self = (j_iK1 == i)
        if np.any(is_self):
            j_iK = np.empty((Nref, self.k), dtype=np.int64)
            D2_iK = np.empty((Nref, self.k), dtype=np.float64)
            for ii in range(Nref):
                keep = (j_iK1[ii] != ii)
                jj = j_iK1[ii][keep][: self.k]
                dd = D2_iK1[ii][keep][: self.k]
                if jj.shape[0] < self.k:
                    pad = self.k - jj.shape[0]
                    jj = np.pad(jj, (0, pad), mode="edge")
                    dd = np.pad(dd, (0, pad), mode="edge")
                j_iK[ii] = jj
                D2_iK[ii] = dd
        else:
            j_iK = j_iK1[:, : self.k].astype(np.int64, copy=False)
            D2_iK = D2_iK1[:, : self.k].astype(np.float64, copy=False)

        # ---- eps from kNN statistics ----
        if eps is None:
            eps_hat = median_eps_from_knn_d2(D2_iK, use_kth=bool(eps_use_kth))
        else:
            eps_hat = float(eps)
        eps_hat *= float(eps_mul)
        if eps_hat <= 0:
            raise ValueError(f"eps must be > 0, got {eps_hat}")
        self.eps = float(eps_hat)
        self.ε = self.eps  # unicode alias

        # -------------------------
        # 1) Warm start: sparse kNN DMAP operator + eigsh
        # -------------------------
        K_iK = np.exp(-self.beta * (D2_iK / self.eps)).astype(np.float64, copy=False)

        indptr = (np.arange(Nref + 1, dtype=np.int64) * self.k)
        indices = j_iK.reshape(-1).astype(np.int64, copy=False)
        data = K_iK.reshape(-1)

        K_ij = sp.csr_matrix((data, indices, indptr), shape=(Nref, Nref), dtype=np.float64)

        # symmetrize
        if self.sym == "max":
            K_ij = K_ij.maximum(K_ij.T)
        elif self.sym == "mean":
            K_ij = (K_ij + K_ij.T) * 0.5
        else:
            raise ValueError(f"Unknown sym={self.sym!r}")

        # degrees q_i and qalpha_i (warm)
        q_i_warm = np.asarray(K_ij.sum(axis=1)).ravel()
        q_i_warm = np.maximum(q_i_warm, 1e-30)
        qalpha_i_warm = np.maximum(np.power(q_i_warm, self.alpha), 1e-30)

        Qinv = sp.diags(1.0 / qalpha_i_warm, format="csr")
        Kalpha_ij = Qinv @ K_ij @ Qinv

        d_i_warm = np.asarray(Kalpha_ij.sum(axis=1)).ravel()
        d_i_warm = np.maximum(d_i_warm, 1e-30)

        Dinv_sqrt = sp.diags(1.0 / np.sqrt(d_i_warm), format="csr")
        A_ij = Dinv_sqrt @ Kalpha_ij @ Dinv_sqrt

        nev = self.d + (1 if self.drop_trivial else 0)
        v0 = rng.normal(size=Nref).astype(np.float64)
        lam0, u0 = eigsh(A_ij, k=nev, which="LA", v0=v0)

        ord0 = np.argsort(lam0)[::-1]
        lam0 = lam0[ord0]
        u0 = u0[:, ord0]

        # LOBPCG warm-start block (orthonormalize)
        X0, _ = np.linalg.qr(u0.astype(np.float64, copy=False))

        # -------------------------
        # 2) Optional refinement: streaming dense LOBPCG on dense PSD operator
        # -------------------------
        if self.refine_dense:
            # full dense K uses all pairs; streaming avoids materializing K
            self._R2_i = np.sum(self.R_iX.astype(np.float64) ** 2, axis=1)  # (Nref,)

            ones = np.ones((Nref, 1), dtype=np.float64)
            q_i = self._K_matmat_dense(ones).ravel()
            q_i = np.maximum(q_i, 1e-30)
            qalpha_i = np.maximum(np.power(q_i, self.alpha), 1e-30)
            u_i = 1.0 / qalpha_i  # q^{-alpha}

            Ku = self._K_matmat_dense(u_i[:, None]).ravel()
            d_i = np.maximum(u_i * Ku, 1e-30)
            s_i = 1.0 / np.sqrt(d_i)

            def A_matmat(V: np.ndarray) -> np.ndarray:
                V = V.astype(np.float64, copy=False)
                V1 = s_i[:, None] * V
                V2 = u_i[:, None] * V1
                V3 = self._K_matmat_dense(V2)
                V4 = u_i[:, None] * V3
                V5 = s_i[:, None] * V4
                return V5

            Aop = LinearOperator(
                (Nref, Nref),
                matvec=lambda v: A_matmat(v[:, None])[:, 0],
                matmat=A_matmat,
                dtype=np.float64,
            )

            try:
                lam, u = lobpcg(
                    Aop,
                    X0,
                    largest=True,
                    maxiter=self.lobpcg_maxiter,
                    tol=self.lobpcg_tol,
                )
                ord1 = np.argsort(lam)[::-1]
                lam = lam[ord1]
                u = u[:, ord1]

                self.q_i = q_i.astype(np.float64, copy=False)
                self.qalpha_i = qalpha_i.astype(np.float64, copy=False)
                self.d_i = d_i.astype(np.float64, copy=False)
            except Exception:
                # fallback to warm start if refinement fails
                lam, u = lam0, u0
                self.q_i = q_i_warm.astype(np.float64, copy=False)
                self.qalpha_i = qalpha_i_warm.astype(np.float64, copy=False)
                self.d_i = d_i_warm.astype(np.float64, copy=False)
        else:
            lam, u = lam0, u0
            self.q_i = q_i_warm.astype(np.float64, copy=False)
            self.qalpha_i = qalpha_i_warm.astype(np.float64, copy=False)
            self.d_i = d_i_warm.astype(np.float64, copy=False)

        # provide unicode aliases for packers / older code
        self.qα_i = self.qalpha_i
        self.λ_x = lam.astype(np.float64, copy=False)

        # psi and drop trivial
        psi = u / np.sqrt(self.d_i)[:, None]
        if self.drop_trivial:
            lam = lam[1:]
            psi = psi[:, 1:]
            u = u[:, 1:]

        # diffusion coords
        R_ix = psi * (lam ** self.t)[None, :]

        # store
        self.λ_x = lam.astype(np.float64, copy=False)   # (d,)
        self.u_ix = u.astype(np.float64, copy=False)    # (Nref,d)
        self.ψ_ix = psi.astype(np.float64, copy=False)  # (Nref,d)
        self.R_ix = R_ix.astype(np.float64, copy=False) # (Nref,d)
        self.π_i = (self.d_i / self.d_i.sum()).astype(np.float64, copy=False)

        # for Nyström: R_ix / λ_x
        self.R_over_λ_ix = (self.R_ix / self.λ_x[None, :]).astype(np.float64, copy=False)

    # --------- streaming dense kernel primitives (only used if refine_dense=True) ----------

    def _rbf_block(self, Xb: np.ndarray, Xc: np.ndarray, X2b: np.ndarray, X2c: np.ndarray) -> np.ndarray:
        # squared distances: ||b||^2 + ||c||^2 - 2 b c^T
        G = Xb @ Xc.T
        D2 = np.maximum(X2b[:, None] + X2c[None, :] - 2.0 * G, 0.0)
        return np.exp(-self.beta * (D2 / self.eps))

    def _K_matmat_dense(self, V: np.ndarray) -> np.ndarray:
        """
        Streaming matmat for dense K:
          out = K @ V
        Does NOT materialize K. Optionally exploits symmetry by only computing upper-tri tiles.
        """
        X = self.R_iX.astype(np.float64, copy=False)
        X2 = self._R2_i
        N = X.shape[0]
        bs = self.stream_block
        V = V.astype(np.float64, copy=False)
        out = np.zeros((N, V.shape[1]), dtype=np.float64)

        if not self.use_symmetry:
            for i0 in range(0, N, bs):
                i1 = min(N, i0 + bs)
                Xi = X[i0:i1]
                X2i = X2[i0:i1]
                acc = np.zeros((i1 - i0, V.shape[1]), dtype=np.float64)
                for j0 in range(0, N, bs):
                    j1 = min(N, j0 + bs)
                    Xj = X[j0:j1]
                    X2j = X2[j0:j1]
                    Kij = self._rbf_block(Xi, Xj, X2i, X2j)
                    acc += Kij @ V[j0:j1]
                out[i0:i1] = acc
            return out

        # symmetric tiling
        for i0 in range(0, N, bs):
            i1 = min(N, i0 + bs)
            Xi = X[i0:i1]
            X2i = X2[i0:i1]
            Vi = V[i0:i1]

            # diagonal tile
            Kii = self._rbf_block(Xi, Xi, X2i, X2i)
            out[i0:i1] += Kii @ Vi

            for j0 in range(i1, N, bs):
                j1 = min(N, j0 + bs)
                Xj = X[j0:j1]
                X2j = X2[j0:j1]
                Vj = V[j0:j1]

                Kij = self._rbf_block(Xi, Xj, X2i, X2j)
                out[i0:i1] += Kij @ Vj
                out[j0:j1] += Kij.T @ Vi

        return out

    # --------- Nyström embedding ----------

    def __call__(self, R_aX: Union[np.ndarray, list], *, batch_size: Optional[int] = None) -> np.ndarray:
        R_aX = np.asarray(R_aX)
        single = (R_aX.ndim == 1)
        if single:
            R_aX = R_aX[None, :]

        R_aX = np.ascontiguousarray(R_aX.astype(self.dtype, copy=False))

        if batch_size is None:
            R_ax = self._embed(R_aX)
        else:
            bs = int(batch_size)
            out = []
            for s in range(0, R_aX.shape[0], bs):
                out.append(self._embed(R_aX[s:s + bs]))
            R_ax = np.vstack(out)

        return R_ax[0] if single else R_ax

    def _embed(self, R_aX: np.ndarray) -> np.ndarray:
        # kNN for novel points
        j_aK, D2_aK = self.ann.search(R_aX, self.k)  # (a,k)

        K_ai = np.exp(-self.beta * (D2_aK.astype(np.float64) / self.eps))  # (a,k)

        q_a = np.maximum(K_ai.sum(axis=1), 1e-30)
        qalpha_a = np.maximum(np.power(q_a, self.alpha), 1e-30)

        qalpha_i = np.maximum(self.qalpha_i[j_aK], 1e-30)
        Kalpha_ai = K_ai / (qalpha_a[:, None] * qalpha_i)

        d_a = np.maximum(Kalpha_ai.sum(axis=1), 1e-30)
        P_ai = Kalpha_ai / d_a[:, None]

        R_over = self.R_over_λ_ix[j_aK, :]  # (a,k,d)
        R_ax = (P_ai[:, :, None] * R_over).sum(axis=1)
        return R_ax


__all__ = ["DMAP", "k_ideal"]