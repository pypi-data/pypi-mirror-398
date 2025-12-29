from typing import cast, Literal
from dataclasses import dataclass

from riskit.type import jaxtyped
from riskit.compute.backend.accelerated import JaxUncertainty, JaxUncertaintySamples

from jax import Array as JaxArray
from jaxtyping import Float, PRNGKeyArray
from numtypes import Dims, Shape, Array

import jax
import jax.numpy as jnp
import jax.random as jrandom


@jaxtyped
@dataclass(kw_only=True)
class JaxGaussian[V: int, D: int](JaxUncertainty[Dims[V, D]]):
    mean: Float[JaxArray, "V D"]
    covariance: Float[JaxArray, "V D D"]
    key: PRNGKeyArray

    @staticmethod
    def create[V_: int, D_: int](
        *,
        mean: Float[JaxArray, "V D"] | Array[Dims[V_, D_]],
        covariance: Float[JaxArray, "V D D"] | Array[Dims[V_, D_, D_]],
        seed: int = 42,
        variables: V_ | None = None,
        dimensions: D_ | None = None,
    ) -> "JaxGaussian[V_, D_]":
        return JaxGaussian(
            mean=jnp.asarray(mean),
            covariance=jnp.asarray(covariance),
            key=jrandom.key(seed),
        )

    def sample[N: int](self, count: N) -> JaxUncertaintySamples[Dims[V, D], N]:
        self.key, samples = sample_gaussian(
            key=self.key, mean=self.mean, covariance=self.covariance, count=count
        )

        return samples

    @property
    def shape(self) -> Dims[V, D]:
        return cast(Dims[V, D], self.mean.shape)


@jaxtyped
@dataclass(kw_only=True)
class JaxUniform[ShapeT: Shape](JaxUncertainty[ShapeT]):
    lower: Float[JaxArray, "*S"]
    upper: Float[JaxArray, "*S"]
    key: PRNGKeyArray

    @staticmethod
    def create[S: Shape](
        *,
        lower: Float[JaxArray, "*S"] | Array[S],
        upper: Float[JaxArray, "*S"] | Array[S],
        seed: int = 42,
        shape: S | None = None,
    ) -> "JaxUniform[S]":
        return JaxUniform(
            lower=jnp.asarray(lower), upper=jnp.asarray(upper), key=jrandom.key(seed)
        )

    def __post_init__(self) -> None:
        assert uniform_bounds_are_valid(lower=self.lower, upper=self.upper)

    def sample[N: int](self, count: N) -> JaxUncertaintySamples[ShapeT, N]:
        self.key, samples = sample_uniform(
            key=self.key,
            lower=self.lower,
            upper=self.upper,
            count=count,
            shape=self.shape,
        )

        return samples

    @property
    def shape(self) -> ShapeT:
        return cast(ShapeT, self.lower.shape)


@jax.jit(static_argnames=("count",))
@jaxtyped
def sample_gaussian(
    *,
    key: PRNGKeyArray,
    mean: Float[JaxArray, "V D"],
    covariance: Float[JaxArray, "V D D"],
    count: int,
) -> tuple[PRNGKeyArray, Float[JaxArray, "V D N"]]:
    key, subkey = jrandom.split(key)
    keys = jrandom.split(subkey, mean.shape[0])

    samples = jax.vmap(
        lambda k, m, c: jrandom.multivariate_normal(k, m, c, shape=(count,))
    )(keys, mean, covariance)

    return key, samples.transpose(0, 2, 1)


@jax.jit(static_argnames=("count", "shape"))
@jaxtyped
def sample_uniform(
    *,
    key: PRNGKeyArray,
    lower: Float[JaxArray, "*S"],
    upper: Float[JaxArray, "*S"],
    count: int,
    shape: tuple[int, ...],
) -> tuple[PRNGKeyArray, Float[JaxArray, "*S N"]]:
    key, subkey = jrandom.split(key)
    samples = roll_axes_left(
        jrandom.uniform(subkey, shape=(count, *shape), minval=lower, maxval=upper)
    )

    return key, samples


@jax.jit
@jaxtyped
def roll_axes_left(array: Float[JaxArray, "..."]) -> Float[JaxArray, "..."]:
    rest = array.shape[1:]
    return array.transpose(*range(1, len(rest) + 1), 0)


@jax.jit
@jaxtyped
def uniform_bounds_are_valid(
    *, lower: Float[JaxArray, "*S"], upper: Float[JaxArray, "*S"]
) -> Literal[True]:
    valid = jnp.all(upper >= lower)
    jax.debug.callback(report_invalid_bounds, valid, lower, upper)
    return True


def report_invalid_bounds(
    valid: bool, lower: Float[JaxArray, "*S"], upper: Float[JaxArray, "*S"]
) -> None:
    if not valid:
        print(
            f"All upper bounds must be greater than lower bounds. Got lower: {lower}, upper: {upper}."
        )
