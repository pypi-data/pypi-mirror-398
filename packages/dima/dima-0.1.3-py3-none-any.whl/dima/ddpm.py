# src/dima/ddpm.py
from __future__ import annotations

from typing import Any, Optional

import jax
import jax.numpy as jnp
from jax import random

from flax import linen as nn
from flax.training import train_state
from flax import struct
import optax


# ------------------------------
# Schedules & embeddings
# ------------------------------
def cosine_schedule(T: int, s: float = 0.008):
    """
    Nichol & Dhariwal cosine schedule.

    Returns:
        alpha:     (T,)
        beta:      (T,)
        alpha_bar: (T,)
    """
    steps = jnp.arange(T + 1, dtype=jnp.float32)
    f = jnp.cos(((steps / T + s) / (1.0 + s)) * jnp.pi / 2.0) ** 2
    alpha_bar_all = f / f[0]
    alpha_bar = alpha_bar_all[1:]  # (T,)
    alpha = alpha_bar / jnp.concatenate([jnp.array([1.0], dtype=jnp.float32), alpha_bar[:-1]])
    beta = 1.0 - alpha
    return alpha, beta, alpha_bar


def sinusoidal_embedding(t_idx: jnp.ndarray, dim: int) -> jnp.ndarray:
    """
    t_idx: (B,1) int32
    returns: (B,dim)
    """
    if t_idx.ndim != 2 or t_idx.shape[1] != 1:
        raise ValueError("t_idx must have shape (B,1)")
    t = t_idx.astype(jnp.float32)
    half = dim // 2
    denom = float(max(half - 1, 1))
    freqs = jnp.exp(-jnp.log(10_000.0) * jnp.arange(half, dtype=jnp.float32) / denom)
    args = t * freqs
    emb = jnp.concatenate([jnp.sin(args), jnp.cos(args)], axis=-1)
    if dim % 2 == 1:
        emb = jnp.pad(emb, ((0, 0), (0, 1)))
    return emb


# ------------------------------
# Model: epsilon predictor
# ------------------------------
class EpsMLP(nn.Module):
    """Simple MLP epsilon-predictor for DDPM in R^D."""
    hidden: int
    t_dim: int
    data_dim: int

    @nn.compact
    def __call__(self, x: jnp.ndarray, t_idx: jnp.ndarray) -> jnp.ndarray:
        # x: (B,D), t_idx: (B,1)
        t_emb = sinusoidal_embedding(t_idx, self.t_dim)
        t_h = nn.Dense(self.hidden)(t_emb)
        t_h = nn.gelu(t_h)

        h = nn.Dense(self.hidden)(x)
        h = nn.gelu(h + t_h)

        t_h2 = nn.Dense(self.hidden)(t_h)
        h = nn.Dense(self.hidden)(h)
        h = nn.gelu(h + t_h2)

        out = nn.Dense(self.data_dim)(h)
        return out


# ------------------------------
# TrainState with EMA
# ------------------------------
@struct.dataclass
class TrainStateEMA(train_state.TrainState):
    """Flax TrainState extended with EMA params."""
    ema_params: Any = struct.field(pytree_node=True)

    def apply_gradients(self, *, grads, ema_decay: float):
        updates, new_opt_state = self.tx.update(grads, self.opt_state, self.params)
        new_params = optax.apply_updates(self.params, updates)
        new_ema = optax.incremental_update(new_params, self.ema_params, step_size=1.0 - ema_decay)
        return self.replace(
            step=self.step + 1,
            params=new_params,
            opt_state=new_opt_state,
            ema_params=new_ema,
        )


# ------------------------------
# DDPM
# ------------------------------
class DDPM:
    """
    DDPM for D-dimensional latents.

    API expected by your DIMA wrapper:
      - DDPM(Z_train, ...): trains in __init__ (n_iter can be 0 to skip)
      - refine_latents(z0, t_start, key, add_noise) -> z_refined
      - __call__(...) delegates to refine_latents
      - sample(N) -> latent samples
      - attributes: state.params, state.ema_params, T, D, model.hidden, model.t_dim, beta_max, eps
    """

    def __init__(
        self,
        Z_iX: jnp.ndarray,
        *,
        T: int = 100,
        hidden_dim: int = 128,
        t_embed_dim: int = 64,
        learning_rate: float = 1e-3,
        n_iter: int = 20_000,
        ema_decay: float = 0.999,
        beta_max: float = 0.02,
        batch_size: Optional[int] = None,
        key: jax.Array = random.PRNGKey(0),
        verbose_every: int = 0,
        eps: float = 1e-5,
    ):
        Z_iX = jnp.asarray(Z_iX, dtype=jnp.float32)
        if Z_iX.ndim != 2:
            raise ValueError("Z_iX must be 2D (N,D).")

        self.D = int(Z_iX.shape[1])
        self.T = int(T)
        self.key = key
        self.ema_decay = float(ema_decay)
        self.batch_size = batch_size
        self.verbose_every = int(verbose_every)
        self.eps = float(eps)
        self.beta_max = float(beta_max)

        # schedule (cosine, clipped by beta_max)
        alpha, beta, alpha_bar = cosine_schedule(self.T)
        beta = jnp.minimum(beta, self.beta_max)
        alpha = 1.0 - beta
        alpha_bar = jnp.cumprod(alpha)

        self.alpha_s = alpha.astype(jnp.float32)
        self.beta_s = beta.astype(jnp.float32)
        self.alpha_bar_s = alpha_bar.astype(jnp.float32)

        # model + optimizer + EMA
        self.model = EpsMLP(hidden=int(hidden_dim), t_dim=int(t_embed_dim), data_dim=self.D)

        params = self.model.init(
            self.key,
            jnp.zeros((1, self.D), dtype=jnp.float32),
            jnp.zeros((1, 1), dtype=jnp.int32),
        )["params"]

        tx = optax.adam(float(learning_rate))
        self.state = TrainStateEMA.create(apply_fn=self.model.apply, params=params, tx=tx, ema_params=params)

        # train
        if int(n_iter) > 0:
            self._train(Z_iX, int(n_iter))

    # ---------- training ----------
    @staticmethod
    def _loss(params, apply_fn, x_t, t_idx, eps_true):
        eps_pred = apply_fn({"params": params}, x_t, t_idx)
        return jnp.mean((eps_pred - eps_true) ** 2)

    @staticmethod
    @jax.jit
    def _train_step(
        state: TrainStateEMA,
        x0_batch: jnp.ndarray,
        key: jax.Array,
        alpha_bar_s: jnp.ndarray,
        ema_decay: float,
        eps: float,
    ):
        B = x0_batch.shape[0]
        key, k_eps, k_t = random.split(key, 3)

        eps_noise = random.normal(k_eps, shape=x0_batch.shape)  # (B,D)
        t_idx = random.randint(k_t, shape=(B, 1), minval=0, maxval=alpha_bar_s.shape[0])

        a_bar_t = jnp.take(alpha_bar_s, t_idx.squeeze(-1))[:, None]
        a_bar_t = jnp.clip(a_bar_t, eps, 1.0)

        x_t = jnp.sqrt(a_bar_t) * x0_batch + jnp.sqrt(1.0 - a_bar_t) * eps_noise

        def loss_fn(p):
            return DDPM._loss(p, state.apply_fn, x_t, t_idx, eps_noise)

        loss, grads = jax.value_and_grad(loss_fn)(state.params)
        new_state = state.apply_gradients(grads=grads, ema_decay=ema_decay)
        return new_state, loss, key

    def _train(self, Z_iX: jnp.ndarray, n_iter: int):
        N = int(Z_iX.shape[0])
        bs = N if (self.batch_size is None) else min(int(self.batch_size), N)

        for it in range(n_iter):
            if bs >= N:
                batch = Z_iX
            else:
                self.key, k_perm = random.split(self.key)
                idx = random.permutation(k_perm, N)[:bs]
                batch = Z_iX[idx]

            self.state, loss, self.key = self._train_step(
                self.state,
                batch,
                self.key,
                self.alpha_bar_s,
                self.ema_decay,
                self.eps,
            )

            if self.verbose_every and (it % self.verbose_every == 0 or it == n_iter - 1):
                print(f"iter {it:6d}  loss {float(loss):.6f}", end="\r")

        if self.verbose_every:
            print("\ntraining complete.")

    # ---------- diffusion utilities ----------
    @staticmethod
    def _posterior_variance(alpha_s, beta_s, alpha_bar_s, t):
        a_bar_t = alpha_bar_s[t]
        a_bar_prev = jnp.where(t > 0, alpha_bar_s[t - 1], jnp.array(1.0, dtype=alpha_bar_s.dtype))
        return ((1.0 - a_bar_prev) / (1.0 - a_bar_t)) * beta_s[t]

    @staticmethod
    def _make_sampler_step(params_ema, apply_fn, alpha_s, beta_s, alpha_bar_s, eps: float):
        @jax.jit
        def step(carry, _):
            key, t, x = carry  # x: (B,D)
            key, k = random.split(key)

            alpha_t = jnp.clip(alpha_s[t], eps, 1.0)
            a_bar_t = jnp.clip(alpha_bar_s[t], eps, 1.0)

            sqrt_alpha = jnp.sqrt(alpha_t)
            sqrt_one_minus_a_bar = jnp.sqrt(jnp.clip(1.0 - a_bar_t, eps, 1.0))

            B = x.shape[0]
            t_batch = jnp.full((B, 1), t, dtype=jnp.int32)
            eps_pred = apply_fn({"params": params_ema}, x, t_batch)  # (B,D)

            # predict x0
            x0_hat = (x - sqrt_one_minus_a_bar * eps_pred) / jnp.sqrt(a_bar_t)

            a_bar_prev = jnp.where(t > 0, alpha_bar_s[t - 1], jnp.array(1.0, dtype=alpha_bar_s.dtype))
            denom = jnp.clip(1.0 - a_bar_t, eps, 1.0)

            coef1 = jnp.sqrt(jnp.clip(a_bar_prev, eps, 1.0)) * beta_s[t] / denom
            coef2 = sqrt_alpha * (1.0 - a_bar_prev) / denom

            mean = coef1 * x0_hat + coef2 * x

            beta_tilde = DDPM._posterior_variance(alpha_s, beta_s, alpha_bar_s, t)
            sigma = jnp.sqrt(jnp.clip(beta_tilde, 0.0, 1.0))

            z = random.normal(k, x.shape)
            z = jnp.where(t == 0, 0.0, z)
            x_prev = mean + sigma * z

            return (key, t - 1, x_prev), x_prev

        return step

    # ---------- API ----------
    def refine_latents(
        self,
        z0: jnp.ndarray,
        t_start: int = 10,
        key: Optional[jax.Array] = None,
        add_noise: bool = True,
    ) -> jnp.ndarray:
        """
        Refine latents by:
          (optional) forward-noise z0 to step t_start
          reverse-diffuse from t_start -> 0 using EMA params.
        """
        z0 = jnp.asarray(z0, dtype=jnp.float32)
        if z0.ndim != 2 or z0.shape[1] != self.D:
            raise ValueError(f"z0 must have shape (B,{self.D}).")
        if not (0 <= int(t_start) < self.T):
            raise ValueError(f"t_start must be in [0, {self.T-1}]")

        t_start = int(t_start)

        if key is None:
            self.key, key = random.split(self.key)
        else:
            # advance internal RNG too
            self.key, _ = random.split(key)

        # forward diffuse to t_start
        key, k_eps = random.split(key)
        eps_noise = random.normal(k_eps, z0.shape)

        a_bar_t = jnp.clip(self.alpha_bar_s[t_start], self.eps, 1.0)
        if add_noise:
            z_t = jnp.sqrt(a_bar_t) * z0 + jnp.sqrt(1.0 - a_bar_t) * eps_noise
        else:
            z_t = z0

        step = self._make_sampler_step(
            self.state.ema_params,
            self.state.apply_fn,
            self.alpha_s,
            self.beta_s,
            self.alpha_bar_s,
            self.eps,
        )

        (final_key, _, _), trace = jax.lax.scan(
            step,
            (key, t_start, z_t),
            xs=None,
            length=t_start + 1,
        )
        self.key = final_key
        return trace[-1]

    def __call__(
        self,
        z0: jnp.ndarray,
        t_start: int = 10,
        key: Optional[jax.Array] = None,
        add_noise: bool = True,
    ) -> jnp.ndarray:
        return self.refine_latents(z0, t_start=t_start, key=key, add_noise=add_noise)

    def reverse_from_T(self, x_T: jnp.ndarray) -> jnp.ndarray:
        x_T = jnp.asarray(x_T, dtype=jnp.float32)
        if x_T.ndim != 2 or x_T.shape[1] != self.D:
            raise ValueError(f"x_T must have shape (B,{self.D}).")

        step = self._make_sampler_step(
            self.state.ema_params,
            self.state.apply_fn,
            self.alpha_s,
            self.beta_s,
            self.alpha_bar_s,
            self.eps,
        )
        self.key, k0 = random.split(self.key)
        (_, _, _), trace = jax.lax.scan(
            step,
            (k0, self.T - 1, x_T),
            xs=None,
            length=self.T,
        )
        return trace[-1]

    def sample(self, N: int = 10_000) -> jnp.ndarray:
        self.key, k = random.split(self.key)
        noise = random.normal(k, (int(N), self.D))
        return self.reverse_from_T(noise)


__all__ = ["DDPM", "EpsMLP", "cosine_schedule", "sinusoidal_embedding"]