from typing import Tuple, Union

import equinox as eqx
import jax.numpy as jnp
from jaxtyping import Array


class StreamNormalizer(eqx.Module):
    mean_index: eqx.nn.StateIndex
    var_index: eqx.nn.StateIndex
    count_index: eqx.nn.StateIndex

    def __init__(self, shape: Union[int, Tuple[int, ...]]):
        if isinstance(shape, int):
            shape = (shape,)
        self.mean_index = eqx.nn.StateIndex(jnp.zeros(shape))
        self.var_index = eqx.nn.StateIndex(jnp.ones(shape))
        self.count_index = eqx.nn.StateIndex(0)

    def __call__(self, x: Array, state: eqx.nn.State) -> Array:
        """center and scale"""
        return (x - state.get(self.mean_index)) / jnp.sqrt(
            state.get(self.var_index) + 1e-8
        )

    def center(self, x: Array, state: eqx.nn.State) -> Array:
        return x - state.get(self.mean_index)

    def update(self, x: Array, state: eqx.nn.State) -> eqx.nn.State:
        """NOTE: this method operates on a batch of vectors"""
        batch_mean = jnp.mean(x, axis=0)
        batch_var = jnp.var(x, axis=0)
        batch_count = x.shape[0]

        mean = state.get(self.mean_index)
        var = state.get(self.var_index)
        count = state.get(self.count_index)

        delta = batch_mean - mean
        tot_count = count + batch_count

        new_mean = mean + delta * batch_count / tot_count
        m_a = var * count
        m_b = batch_var * batch_count
        M2 = m_a + m_b + jnp.square(delta) * batch_count * count / tot_count
        new_var = M2 / tot_count
        new_count = tot_count

        new_state = (
            state.set(self.mean_index, new_mean)
            .set(self.var_index, new_var)
            .set(self.count_index, new_count)
        )
        return new_state


class EMAPercScaler(eqx.Module):
    """EMA scale by difference of percentiles (Dreamer-v3 tricks for Policy Gradient (REINFORCE))"""

    low_index: eqx.nn.StateIndex
    high_index: eqx.nn.StateIndex

    low_p: float = eqx.field(static=True)
    high_p: float = eqx.field(static=True)
    tau: float = eqx.field(static=True, default=0.01)

    def __init__(
        self,
        shape: Union[int, Tuple[int, ...]],
        low_p: float = 0.05,
        high_p: float = 0.95,
        tau: float = 0.01,
    ):
        assert 0 <= low_p < high_p <= 1, (
            "Percentiles must be in [0, 1] and low_p < high_p"
        )
        if isinstance(shape, int):
            shape = (shape,)

        self.low_p = low_p
        self.high_p = high_p
        self.tau = tau

        self.low_index = eqx.nn.StateIndex(jnp.full(shape, jnp.nan))
        self.high_index = eqx.nn.StateIndex(jnp.full(shape, jnp.nan))

    def __call__(self, x: Array, state: eqx.nn.State) -> Array:
        """center and scale"""
        low_p = state.get(self.low_index)
        high_p = state.get(self.high_index)
        scale = jnp.nan_to_num(high_p - low_p, nan=1.0)
        return x / jnp.maximum(scale, 1.0)

    def update(self, x: Array, state: eqx.nn.State) -> eqx.nn.State:
        """NOTE: this method operates on a batch of vectors"""
        batch_low = jnp.percentile(x, self.low_p, axis=0)
        batch_high = jnp.percentile(x, self.high_p, axis=0)

        prev_low = state.get(self.low_index)
        prev_high = state.get(self.high_index)

        new_low = jnp.where(
            jnp.isnan(prev_low),
            batch_low,
            prev_low + self.tau * (batch_low - prev_low),
        )
        new_high = jnp.where(
            jnp.isnan(prev_high),
            batch_high,
            prev_high + self.tau * (batch_high - prev_high),
        )
        new_state = state.set(self.low_index, new_low).set(self.high_index, new_high)
        return new_state
