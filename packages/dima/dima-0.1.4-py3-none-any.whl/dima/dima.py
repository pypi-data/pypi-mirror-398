# src/dima/dima.py
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional, Union

import numpy as np

import jax
import jax.numpy as jnp
from jax import random

from flax import serialization as flax_ser

from .dmap import DMAP
from .gplm import GPLM
from .ddpm import DDPM
from .ann import ANNBackend, make_ann


# ----------------------------
# Optional: Hugging Face Hub
# ----------------------------
try:
    from huggingface_hub import HfApi, HfFolder, upload_file, hf_hub_download
    _HAS_HF = True
except Exception:
    _HAS_HF = False


def _select_device(prefer: str = "auto"):
    """
    Safe JAX device selection.
    prefer: "auto" | "gpu" | "cpu"
    """
    prefer = (prefer or "auto").lower()
    devs = jax.devices()
    gpu = [d for d in devs if d.platform == "gpu"]
    cpu = [d for d in devs if d.platform == "cpu"]

    if prefer in ("auto", "gpu"):
        return gpu[0] if gpu else (cpu[0] if cpu else devs[0])
    if prefer == "cpu":
        return cpu[0] if cpu else devs[0]
    # unknown -> auto
    return gpu[0] if gpu else (cpu[0] if cpu else devs[0])


def _np_dtype_str(x) -> str:
    try:
        return str(np.dtype(x))
    except Exception:
        return "float32"


# ----------------------------
# Frozen inference-only models
# ----------------------------
class FrozenDMAP:
    """
    Inference-only Nyström DMAP embedder built from saved DMAP state.
    Uses kNN in ambient space against reference points.
    """

    def __init__(
        self,
        state: Dict[str, Any],
        *,
        ann_backend: ANNBackend = "auto",
        ann_params: Optional[Dict[str, Any]] = None,
        n_jobs: int = -1,
    ):
        self.k = int(state["k"])
        self.beta = float(state["beta"])
        self.alpha = float(state["alpha"])
        self.eps = float(state["eps"])
        self.dtype = np.dtype(state.get("dtype", "float32"))

        self.R_iX = np.ascontiguousarray(np.asarray(state["R_iX"]).astype(self.dtype, copy=False))
        self.qalpha_i = np.asarray(state["qalpha_i"], dtype=np.float64)
        self.R_over_lam_ix = np.asarray(state["R_over_lam_ix"], dtype=np.float64)  # (Nref,d)

        self.ann, self.ann_backend = make_ann(ann_backend, ann_params=ann_params, n_jobs=n_jobs)
        self.ann.build(self.R_iX)

    def __call__(self, R_aX: Union[np.ndarray, list], *, batch_size: Optional[int] = None) -> np.ndarray:
        R_aX = np.asarray(R_aX)
        single = (R_aX.ndim == 1)
        if single:
            R_aX = R_aX[None, :]

        R_aX = np.ascontiguousarray(R_aX.astype(self.dtype, copy=False))

        if batch_size is None:
            Z = self._embed(R_aX)
        else:
            out = []
            bs = int(batch_size)
            for s in range(0, R_aX.shape[0], bs):
                out.append(self._embed(R_aX[s : s + bs]))
            Z = np.vstack(out)

        return Z[0] if single else Z

    def _embed(self, R_aX: np.ndarray) -> np.ndarray:
        j_aK, D2_aK = self.ann.search(R_aX, self.k)  # (a,k)
        K_ai = np.exp(-self.beta * (D2_aK.astype(np.float64) / self.eps))  # (a,k)

        q_a = np.maximum(K_ai.sum(axis=1), 1e-30)
        qalpha_a = np.maximum(np.power(q_a, self.alpha), 1e-30)

        qalpha_i = np.maximum(self.qalpha_i[j_aK], 1e-30)
        Kalpha_ai = K_ai / (qalpha_a[:, None] * qalpha_i)

        d_a = np.maximum(Kalpha_ai.sum(axis=1), 1e-30)
        P_ai = Kalpha_ai / d_a[:, None]

        R_over = self.R_over_lam_ix[j_aK, :]              # (a,k,d)
        Z_ax = (P_ai[:, :, None] * R_over).sum(axis=1)    # (a,d)
        return Z_ax


class FrozenGPLM:
    """
    Inference-only GPLM decoder built from saved GPLM state.
    Supports optional pred_k via ANN over inducing points.
    """

    def __init__(
        self,
        state: Dict[str, Any],
        *,
        ann_backend: ANNBackend = "auto",
        ann_params: Optional[Dict[str, Any]] = None,
        n_jobs: int = -1,
    ):
        self.beta = float(state["beta"])
        self.eps = float(state["eps"])
        self.pred_k = None if state.get("pred_k", None) is None else int(state["pred_k"])
        self.dtype = np.dtype(state.get("dtype", "float32"))

        self.mean_X = np.asarray(state["mean_X"], dtype=np.float64)
        self.M_mX = np.asarray(state["M_mX"], dtype=np.float64)

        # latent whitening used at training time
        self.lat_mean_x = np.asarray(state["lat_mean_x"], dtype=np.float64)
        self.lat_std_x = np.asarray(state["lat_std_x"], dtype=np.float64)

        # inducing points in whitened latent space
        self.Z_mx_w = np.ascontiguousarray(np.asarray(state["Z_mx_w"]).astype(np.float64, copy=False))
        self.m = int(self.Z_mx_w.shape[0])

        self.ann_Z, self.ann_backend = make_ann(ann_backend, ann_params=ann_params, n_jobs=n_jobs)
        self.ann_Z.build(self.Z_mx_w.astype(self.dtype, copy=False))

    def __call__(self, R_ax: Union[np.ndarray, list], *, batch_size: Optional[int] = None) -> np.ndarray:
        R_ax = np.asarray(R_ax)
        single = (R_ax.ndim == 1)
        if single:
            R_ax = R_ax[None, :]
        R_ax = np.ascontiguousarray(R_ax.astype(self.dtype, copy=False))

        if batch_size is None:
            Y = self._decode(R_ax)
        else:
            out = []
            bs = int(batch_size)
            for s in range(0, R_ax.shape[0], bs):
                out.append(self._decode(R_ax[s : s + bs]))
            Y = np.vstack(out)

        return Y[0] if single else Y

    @staticmethod
    def _sqdist_ab(A: np.ndarray, B: np.ndarray) -> np.ndarray:
        A = np.asarray(A, dtype=np.float64)
        B = np.asarray(B, dtype=np.float64)
        A2 = np.sum(A * A, axis=1, keepdims=True)
        B2 = np.sum(B * B, axis=1, keepdims=True).T
        G = A @ B.T
        return np.maximum(A2 + B2 - 2.0 * G, 0.0)

    def _decode(self, R_ax: np.ndarray) -> np.ndarray:
        Za = R_ax.astype(np.float64)
        Za_w = (Za - self.lat_mean_x[None, :]) / self.lat_std_x[None, :]

        if self.pred_k is None or self.pred_k >= self.m:
            D2_am = self._sqdist_ab(Za_w, self.Z_mx_w)
            C_am = np.exp(-self.beta * (D2_am / self.eps))
            Y = C_am @ self.M_mX
        else:
            j_aK, D2_aK = self.ann_Z.search(Za_w.astype(self.dtype, copy=False), self.pred_k)
            W = np.exp(-self.beta * (D2_aK.astype(np.float64) / self.eps))      # (a,k)
            M = self.M_mX[j_aK]                                                 # (a,k,D)
            Y = np.sum(W[:, :, None] * M, axis=1)                               # (a,D)

        return Y + self.mean_X[None, :]


# ----------------------------
# Config
# ----------------------------
@dataclass
class DIMAConfig:
    d: int = 32
    ddpm_device: str = "auto"   # "auto" | "cpu" | "gpu"
    # purely informational defaults (actual settings live in kwargs dicts)
    version: str = "0.1.0"


# ----------------------------
# Main wrapper
# ----------------------------
class DIMA:
    """
    DIMA: Diffusion–Intrinsic Manifold Autoencoder

    Pipeline:
      - DMAP encoder (NumPy/SciPy, CPU): ambient -> raw latent
      - GPLM decoder (NumPy/SciPy, CPU): raw latent -> ambient
      - DDPM latent model (JAX/Flax, CPU or GPU): trained on *normalized* latents

    API:
      model = DIMA(R_iX, dmap_kwargs=..., gplm_kwargs=..., ddpm_kwargs=..., ddpm_device="auto")
      Z = model.encode(X)           # normalized latents (jnp on ddpm device)
      Xhat = model.decode(Z)        # ambient (np on CPU), optionally with DDPM refinement
      Xhat2 = model(X)              # polymorphic: ambient -> latent
      Xhat3 = model(Z)              # polymorphic: latent -> ambient (refine=True default)
      Xsamp = model.sample(1000)    # unconditional samples (ambient np)
    """

    def __init__(
        self,
        R_iX: np.ndarray,
        *,
        d: int = 32,
        dmap_kwargs: Optional[Dict[str, Any]] = None,
        gplm_kwargs: Optional[Dict[str, Any]] = None,
        ddpm_kwargs: Optional[Dict[str, Any]] = None,
        ddpm_device: str = "auto",
        key: Optional[jax.Array] = None ):
        self.config = DIMAConfig(d=int(d), ddpm_device=str(ddpm_device))
        self.training_time = 0.0

        t0 = time.time()

        # data
        self.R_iX = np.asarray(R_iX)
        if self.R_iX.ndim != 2:
            raise ValueError("R_iX must be 2D (N,D).")
        self.N, self.D = self.R_iX.shape
        self.d = int(d)

        dmap_kwargs = {} if dmap_kwargs is None else dict(dmap_kwargs)
        gplm_kwargs = {} if gplm_kwargs is None else dict(gplm_kwargs)
        ddpm_kwargs = {} if ddpm_kwargs is None else dict(ddpm_kwargs)

        # choose device for DDPM
        self.ddpm_device = _select_device(self.config.ddpm_device)
        self.cpu_device = _select_device("cpu")

        if key is None:
            key = random.PRNGKey(0)
        self.rng = key

        # -------------------------
        # 1) Train DMAP (CPU)
        # -------------------------
        self.enc = DMAP(self.R_iX, d=self.d, **dmap_kwargs)
        R_ix = np.asarray(self.enc(self.R_iX))  # raw latents (N,d) float64

        # -------------------------
        # 2) Fit latent normalization (ONCE)
        # -------------------------
        self.lat_mean_np = R_ix.mean(axis=0, keepdims=True).astype(np.float64)
        self.lat_std_np = (R_ix.std(axis=0, keepdims=True) + 1e-6).astype(np.float64)

        Z_ix = (R_ix - self.lat_mean_np) / self.lat_std_np  # normalized latents (np)

        # keep norms on ddpm device too
        self.lat_mean_j = jax.device_put(jnp.asarray(self.lat_mean_np, dtype=jnp.float32), self.ddpm_device)
        self.lat_std_j = jax.device_put(jnp.asarray(self.lat_std_np, dtype=jnp.float32), self.ddpm_device)

        # -------------------------
        # 3) Train GPLM (CPU)
        # -------------------------
        self.dec = GPLM(R_ix, self.R_iX, **gplm_kwargs)

        # -------------------------
        # 4) Train DDPM on normalized latents (DDPM device)
        # -------------------------
        Z_ix_j = jax.device_put(jnp.asarray(Z_ix, dtype=jnp.float32), self.ddpm_device)

        # defaults (can be overridden by ddpm_kwargs)
        ddpm_init = dict(
            T=200,
            hidden_dim=128,
            t_embed_dim=64,
            learning_rate=3e-4,
            n_iter=200_000,
            ema_decay=0.999,
            beta_max=0.02,
            batch_size=256,
            key=self.rng,
            verbose_every=0,
            eps=1e-5,
        )
        ddpm_init.update(ddpm_kwargs)

        with jax.default_device(self.ddpm_device):
            self.dm = DDPM(Z_ix_j, **ddpm_init)

        self.training_time = time.time() - t0

    # -------------------------
    # Encode / Decode
    # -------------------------
    def encode(self, R_aX: Union[np.ndarray, jnp.ndarray], *, to_device: bool = True) -> jnp.ndarray:
        """
        ambient -> normalized latent (DDPM space)
        Returns jnp on ddpm_device by default.
        """
        X = np.asarray(R_aX)
        Z_raw = np.asarray(self.enc(X))  # CPU
        Z_norm = (Z_raw - self.lat_mean_np) / self.lat_std_np
        Zj = jnp.asarray(Z_norm, dtype=jnp.float32)
        return jax.device_put(Zj, self.ddpm_device) if to_device else Zj

    def decode(
        self,
        Z_ax: Union[np.ndarray, jnp.ndarray],
        *,
        refine: bool = True,
        t_start: int = 10,
        add_noise: bool = True,
        key: Optional[jax.Array] = None,
        batch_size: Optional[int] = None,
    ) -> np.ndarray:
        """
        normalized latent -> (optional DDPM refine) -> raw latent -> ambient
        Returns numpy array (CPU).
        """
        Z = jnp.asarray(Z_ax, dtype=jnp.float32)
        if Z.ndim == 1:
            Z = Z[None, :]
        Z = jax.device_put(Z, self.ddpm_device)

        if refine:
            Z = self.dm.refine_latents(Z, t_start=int(t_start), key=key, add_noise=bool(add_noise))

        # unnormalize to raw latent (still on device)
        R_ax = (Z * self.lat_std_j) + self.lat_mean_j
        R_ax_np = np.asarray(jax.device_get(R_ax))  # to CPU

        X_hat = self.dec(R_ax_np, batch_size=batch_size)  # CPU decode
        return np.asarray(X_hat)

    def reconstruct(
        self,
        R_aX: Union[np.ndarray, jnp.ndarray],
        *,
        refine: bool = False,
        t_start: int = 10,
        add_noise: bool = True,
        key: Optional[jax.Array] = None,
        batch_size: Optional[int] = None,
    ) -> np.ndarray:
        """Convenience: decode(encode(X))."""
        Z = self.encode(R_aX, to_device=True)
        return self.decode(Z, refine=refine, t_start=t_start, add_noise=add_noise, key=key, batch_size=batch_size)

    def sample(self, n: int, *, decode: bool = True, batch_size: Optional[int] = None) -> Union[jnp.ndarray, np.ndarray]:
        """
        Unconditional samples from latent DDPM.
        If decode=True, returns ambient samples as np.ndarray.
        Otherwise returns normalized latents as jnp.ndarray.
        """
        with jax.default_device(self.ddpm_device):
            Z = self.dm.sample(int(n))
        if not decode:
            return Z
        return self.decode(Z, refine=False, batch_size=batch_size)

    # -------------------------
    # helpers: normalize <-> raw
    # -------------------------
    def _to_np(self, A: Union[np.ndarray, jnp.ndarray]) -> np.ndarray:
        if isinstance(A, jax.Array):
            return np.asarray(jax.device_get(A))
        return np.asarray(A)

    def _norm_to_raw_np(self, Z_ax: np.ndarray) -> np.ndarray:
        # Z_ax: normalized (a,d) -> raw r_ax (a,d)
        return Z_ax * self.lat_std_np + self.lat_mean_np

    def _raw_to_norm_np(self, R_ax: np.ndarray) -> np.ndarray:
        # raw r_ax (a,d) -> normalized (a,d)
        return (R_ax - self.lat_mean_np) / self.lat_std_np

    def _metric_raw_to_norm(self, g_raw_add: np.ndarray) -> np.ndarray:
        # g_norm_xy = sigma_x sigma_y g_raw_xy
        sig = self.lat_std_np.reshape(-1)  # (d,)
        return g_raw_add * (sig[None, :, None] * sig[None, None, :])

    def _jac_raw_to_norm(self, J_raw_aDd: np.ndarray) -> np.ndarray:
        # J_norm_{D,x} = dR/dz_x = dR/dr_y * dr_y/dz_x = J_raw_{D,x} * sigma_x
        sig = self.lat_std_np.reshape(-1)  # (d,)
        return J_raw_aDd * sig[None, None, :]

    # -------------------------
    # new: flow wrapper
    # -------------------------
    def flow(
        self,
        Z_ax: Union[np.ndarray, jnp.ndarray],
        v0_ax: Union[np.ndarray, jnp.ndarray],
        *,
        dt: float = 0.05,
        reg: float = 1e-8,
        keep_speed: bool = True,
        # optional: decode + metric/J outputs at the new point
        decode: bool = True,
        jacobian: bool = False,
        metric: bool = False,
        metric_in: str = "norm",  # "norm" or "raw"
        # optional DDPM projection (stochastic): OFF by default for deterministic geodesics
        refine: bool = False,
        ddpm_kwargs: Optional[Dict[str, Any]] = None,
    ):
        """
        One geodesic step in latent space using GPLM.flow (analytic Christoffels + velocity-Verlet),
        where Z_ax and v0_ax are in *normalized* latent coordinates.

        Returns (if decode=True):
            Xhat_aX, Q_ax, v_ax                  (and optionally J/g depending on flags)
        Returns (if decode=False):
            Q_ax, v_ax
        """
        ddpm_kwargs = {} if ddpm_kwargs is None else dict(ddpm_kwargs)

        Z_np = self._to_np(Z_ax)
        v_np = self._to_np(v0_ax)

        single = (Z_np.ndim == 1)
        if single:
            Z_np = Z_np[None, :]
        if v_np.ndim == 1:
            v_np = v_np[None, :]

        if Z_np.shape != v_np.shape:
            raise ValueError(f"Z_ax and v0_ax must have same shape; got {Z_np.shape} vs {v_np.shape}")

        # normalized -> raw for GPLM.flow
        R_raw = self._norm_to_raw_np(Z_np)                         # (a,d)
        v_raw = v_np * self.lat_std_np                             # (a,d)  (dr/dt = sigma * dz/dt)

        # one step geodesic update in raw coordinates
        Q_raw, v_raw_new = self.dec.flow(R_raw, v_raw, dt=dt, reg=reg, keep_speed=keep_speed)

        # raw -> normalized
        Q_norm = self._raw_to_norm_np(Q_raw)
        v_norm = v_raw_new / self.lat_std_np

        # optional: DDPM projection in normalized coords
        if refine:
            # keep this minimal; adapt to your DDPM API if needed
            Zj = jax.device_put(jnp.asarray(Q_norm, dtype=jnp.float32), self.ddpm_device)
            if hasattr(self.dm, "refine_latents"):
                Zj2 = self.dm.refine_latents(Zj, **ddpm_kwargs)
            else:
                Zj2 = self.dm(Zj, **ddpm_kwargs)
            Q_norm = np.asarray(jax.device_get(Zj2))
            # velocity after projection is ambiguous; keep v as-is in normalized chart

        # return latents on ddpm device (consistent with encode())
        Q_out = jax.device_put(jnp.asarray(Q_norm, dtype=jnp.float32), self.ddpm_device)
        v_out = jax.device_put(jnp.asarray(v_norm, dtype=jnp.float32), self.ddpm_device)

        if not decode:
            if single:
                return Q_out[0], v_out[0]
            return Q_out, v_out

        # decode at Q_norm: need raw coords for GPLM.__call__
        Q_raw2 = self._norm_to_raw_np(np.asarray(Q_norm))

        if (not jacobian) and (not metric):
            Xhat = self.dec(Q_raw2)
            if single:
                return Xhat[0], Q_out[0], v_out[0]
            return Xhat, Q_out, v_out

        # request J and/or g from GPLM in raw coords
        out = self.dec(Q_raw2, jacobian=jacobian, metric=metric)

        # normalize J/g if requested
        if jacobian and metric:
            Xhat, J_raw, g_raw = out
            if metric_in == "norm":
                J_use = self._jac_raw_to_norm(J_raw)
                g_use = self._metric_raw_to_norm(g_raw)
            else:
                J_use, g_use = J_raw, g_raw
            if single:
                return Xhat[0], J_use[0], g_use[0], Q_out[0], v_out[0]
            return Xhat, J_use, g_use, Q_out, v_out

        if jacobian and (not metric):
            Xhat, J_raw = out
            J_use = self._jac_raw_to_norm(J_raw) if metric_in == "norm" else J_raw
            if single:
                return Xhat[0], J_use[0], Q_out[0], v_out[0]
            return Xhat, J_use, Q_out, v_out

        # metric only
        Xhat, g_raw = out
        g_use = self._metric_raw_to_norm(g_raw) if metric_in == "norm" else g_raw
        if single:
            return Xhat[0], g_use[0], Q_out[0], v_out[0]
        return Xhat, g_use, Q_out, v_out

    # -------------------------
    # modify __call__ to support metric/jacobian and velocity
    # -------------------------
    def __call__(
        self,
        R_any: Union[np.ndarray, jnp.ndarray],
        *,
        refine: bool = True,
        jacobian: bool = False,
        metric: bool = False,
        metric_in: str = "norm",     # for latent->ambient: return g in "norm" or "raw"
        velocity: Optional[Union[np.ndarray, jnp.ndarray]] = None,
        dt: float = 0.05,
        reg: float = 1e-8,
        keep_speed: bool = True,
        ddpm_kwargs: Optional[Dict[str, Any]] = None,
    ):
        """
        Polymorphic call:
          - if trailing dim == D: ambient -> normalized latent (jnp on ddpm device)
          - if trailing dim == d: normalized latent -> ambient (np), optionally returning J/g
          - if trailing dim == d and velocity is provided: one flow step then decode

        Returns:
          ambient->latent: Z (jnp)
          latent->ambient:
            - if no velocity: Xhat (or (Xhat,J)/(Xhat,g)/(Xhat,J,g))
            - if velocity:    Xhat, Q, v  (and optionally J/g depending on flags)
        """
        ddpm_kwargs = {} if ddpm_kwargs is None else dict(ddpm_kwargs)

        X = self._to_np(R_any)
        last = X.shape[-1]

        if last == self.D:
            # keep whatever your encode() does; here’s the minimal consistent behavior:
            Z = np.asarray(self.enc(X))                      # raw latents (np)
            Z = (Z - self.lat_mean_np) / self.lat_std_np     # normalized
            return jax.device_put(jnp.asarray(Z, dtype=jnp.float32), self.ddpm_device)

        if last == self.d:
            # If velocity: do one geodesic step (normalized chart), then decode
            if velocity is not None:
                return self.flow(
                    X, velocity,
                    dt=dt, reg=reg, keep_speed=keep_speed,
                    decode=True, jacobian=jacobian, metric=metric, metric_in=metric_in,
                    refine=refine, ddpm_kwargs=ddpm_kwargs,
                )

            # Otherwise: decode directly (optionally refine in normalized coords)
            Z_norm = X
            if refine:
                Zj = jax.device_put(jnp.asarray(Z_norm, dtype=jnp.float32), self.ddpm_device)
                if hasattr(self.dm, "refine_latents"):
                    Zj2 = self.dm.refine_latents(Zj, **ddpm_kwargs)
                else:
                    Zj2 = self.dm(Zj, **ddpm_kwargs)
                Z_norm = np.asarray(jax.device_get(Zj2))

            R_raw = self._norm_to_raw_np(np.asarray(Z_norm))
            out = self.dec(R_raw, jacobian=jacobian, metric=metric)

            if (not jacobian) and (not metric):
                return out

            if jacobian and metric:
                Xhat, J_raw, g_raw = out
                if metric_in == "norm":
                    return Xhat, self._jac_raw_to_norm(J_raw), self._metric_raw_to_norm(g_raw)
                return out

            if jacobian and (not metric):
                Xhat, J_raw = out
                return (Xhat, self._jac_raw_to_norm(J_raw)) if metric_in == "norm" else out

            # metric only
            Xhat, g_raw = out
            return (Xhat, self._metric_raw_to_norm(g_raw)) if metric_in == "norm" else out

        raise ValueError(f"Trailing dim must be D={self.D} (ambient) or d={self.d} (latent), got {last}.")


    # -------------------------
    # Save / Load
    # -------------------------
    def _pack_encoder(self) -> Dict[str, Any]:
        # minimal state for Nyström OOS
        return dict(
            R_iX=np.asarray(self.enc.R_iX),
            qalpha_i=np.asarray(getattr(self.enc, "qalpha_i", getattr(self.enc, "qα_i"))),
            R_over_lam_ix=np.asarray(getattr(self.enc, "R_over_λ_ix", getattr(self.enc, "R_over_lam_ix"))),
            k=int(self.enc.k),
            beta=float(getattr(self.enc, "beta", getattr(self.enc, "β"))),
            alpha=float(getattr(self.enc, "alpha", getattr(self.enc, "α"))),
            eps=float(getattr(self.enc, "eps", getattr(self.enc, "ε"))),
            dtype=_np_dtype_str(getattr(self.enc, "dtype", np.float32)),
        )

    def _pack_decoder(self) -> Dict[str, Any]:
        return dict(
            Z_mx_w=np.asarray(getattr(self.dec, "Z_mx_w", getattr(self.dec, "Z_mx_w", None))),
            M_mX=np.asarray(self.dec.M_mX),
            mean_X=np.asarray(getattr(self.dec, "mean_X", np.zeros((self.D,), dtype=np.float64))),
            lat_mean_x=np.asarray(getattr(self.dec, "lat_mean_x", np.zeros((self.d,), dtype=np.float64))),
            lat_std_x=np.asarray(getattr(self.dec, "lat_std_x", np.ones((self.d,), dtype=np.float64))),
            beta=float(getattr(self.dec, "beta", getattr(self.dec, "β"))),
            eps=float(getattr(self.dec, "eps", getattr(self.dec, "ε"))),
            pred_k=getattr(self.dec, "pred_k", getattr(self.dec, "pred_κ", None)),
            dtype=_np_dtype_str(getattr(self.dec, "dtype", np.float32)),
        )

    def state_dict(self) -> Dict[str, Any]:
        """
        Serializable state (msgpack via flax.serialization).
        """
        dd = dict(
            T=int(self.dm.T),
            D=int(self.dm.D),
            hidden_dim=int(getattr(self.dm.model, "hidden", 128)),
            t_embed_dim=int(getattr(self.dm.model, "t_dim", 64)),
            ema_decay=float(getattr(self.dm, "ema_decay", 0.999)),
            beta_max=float(getattr(self.dm, "beta_max", 0.02)),
            eps=float(getattr(self.dm, "eps", 1e-5)),
            params=self.dm.state.params,
            ema_params=self.dm.state.ema_params,
        )

        state = dict(
            meta=dict(
                N=int(self.N),
                D=int(self.D),
                d=int(self.d),
                training_time=float(self.training_time),
            ),
            config=asdict(self.config),
            latent_norm=dict(
                mean=np.asarray(self.lat_mean_np, dtype=np.float64),
                std=np.asarray(self.lat_std_np, dtype=np.float64),
            ),
            encoder=self._pack_encoder(),
            decoder=self._pack_decoder(),
            ddpm=dd,
        )
        return state

    def save_local(self, weights_file: str = "dima.msgpack", config_file: str = "config.json") -> None:
        state = self.state_dict()
        blob = flax_ser.msgpack_serialize(state)
        with open(weights_file, "wb") as f:
            f.write(blob)
        with open(config_file, "w") as f:
            json.dump(state["config"], f, indent=2)
        return None

    @classmethod
    def load_local(
        cls,
        weights_file: str = "dima.msgpack",
        *,
        ddpm_device: str = "auto",
        ann_backend: ANNBackend = "auto",
        ann_params: Optional[Dict[str, Any]] = None,
        n_jobs: int = -1,
        key: Optional[jax.Array] = None,
    ) -> "DIMA":
        with open(weights_file, "rb") as f:
            state = flax_ser.msgpack_restore(f.read())

        obj = cls.__new__(cls)  # bypass __init__

        obj.config = DIMAConfig(**state["config"])
        obj.ddpm_device = _select_device(ddpm_device)
        obj.cpu_device = _select_device("cpu")
        obj.training_time = float(state["meta"].get("training_time", 0.0))

        obj.N = int(state["meta"]["N"])
        obj.D = int(state["meta"]["D"])
        obj.d = int(state["meta"]["d"])

        # RNG
        if key is None:
            key = random.PRNGKey(0)
        obj.rng = key

        # latent norm
        obj.lat_mean_np = np.asarray(state["latent_norm"]["mean"], dtype=np.float64)
        obj.lat_std_np = np.asarray(state["latent_norm"]["std"], dtype=np.float64)

        obj.lat_mean_j = jax.device_put(jnp.asarray(obj.lat_mean_np, dtype=jnp.float32), obj.ddpm_device)
        obj.lat_std_j = jax.device_put(jnp.asarray(obj.lat_std_np, dtype=jnp.float32), obj.ddpm_device)

        # encoder/decoder frozen
        obj.enc = FrozenDMAP(state["encoder"], ann_backend=ann_backend, ann_params=ann_params, n_jobs=n_jobs)
        obj.dec = FrozenGPLM(state["decoder"], ann_backend=ann_backend, ann_params=ann_params, n_jobs=n_jobs)

        # rebuild DDPM skeleton with dummy data, then load params
        dd = state["ddpm"]
        T = int(dd["T"])
        D = int(dd["D"])
        hidden_dim = int(dd["hidden_dim"])
        t_embed_dim = int(dd["t_embed_dim"])
        ema_decay = float(dd.get("ema_decay", 0.999))
        beta_max = float(dd.get("beta_max", 0.02))
        eps = float(dd.get("eps", 1e-5))

        dummy = jnp.zeros((1, D), dtype=jnp.float32)
        with jax.default_device(obj.ddpm_device):
            obj.dm = DDPM(
                dummy,
                T=T,
                hidden_dim=hidden_dim,
                t_embed_dim=t_embed_dim,
                learning_rate=1e-3,
                n_iter=0,               # skip training on load
                ema_decay=ema_decay,
                beta_max=beta_max,
                batch_size=1,
                key=obj.rng,
                verbose_every=0,
                eps=eps,
            )
            obj.dm.state = obj.dm.state.replace(params=dd["params"], ema_params=dd["ema_params"])

        obj.R_iX = None  # training data not stored by default
        return obj

    # -------------------------
    # Hugging Face helpers
    # -------------------------
    def upload_to_huggingface(
        self,
        repo_id: str,
        *,
        hf_token: Optional[str] = None,
        weights_file: str = "dima.msgpack",
        config_file: str = "config.json",
    ) -> None:
        if not _HAS_HF:
            raise ImportError("huggingface_hub not installed. pip install dima[hf] (or huggingface_hub).")
        if hf_token is not None:
            HfFolder.save_token(hf_token)
        api = HfApi()
        _ = api.whoami(token=hf_token)  # sanity check token (no-op if public)

        self.save_local(weights_file=weights_file, config_file=config_file)
        for fname in (weights_file, config_file):
            upload_file(path_or_fileobj=fname, path_in_repo=fname, repo_id=repo_id, token=hf_token)
        return None

    @classmethod
    def load_from_huggingface(
        cls,
        repo_id: str,
        *,
        hf_token: Optional[str] = None,
        weights_file: str = "dima.msgpack",
        config_file: str = "config.json",
        ddpm_device: str = "auto",
        ann_backend: ANNBackend = "auto",
        ann_params: Optional[Dict[str, Any]] = None,
        n_jobs: int = -1,
        key: Optional[jax.Array] = None,
    ) -> "DIMA":
        if not _HAS_HF:
            raise ImportError("huggingface_hub not installed. pip install dima[hf] (or huggingface_hub).")

        wpath = hf_hub_download(repo_id, weights_file, token=hf_token)
        _ = hf_hub_download(repo_id, config_file, token=hf_token)  # for humans / future-proofing

        return cls.load_local(
            wpath,
            ddpm_device=ddpm_device,
            ann_backend=ann_backend,
            ann_params=ann_params,
            n_jobs=n_jobs,
            key=key,
        )


__all__ = ["DIMA", "DIMAConfig"]
