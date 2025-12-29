from typing import cast
from dataclasses import dataclass

from riskit.compute.backend.basic import NumPyUncertainty, NumPyUncertaintySamples

from numtypes import Array, shape_of, Dims, Shape

import numpy as np


@dataclass(kw_only=True, frozen=True)
class NumPyGaussian[V: int, D: int](NumPyUncertainty[Dims[V, D]]):
    mean: Array[Dims[V, D]]
    covariance: Array[Dims[V, D, D]]
    rng: np.random.Generator

    @staticmethod
    def create[V_: int, D_: int](
        *,
        mean: Array[Dims[V_, D_]],
        covariance: Array[Dims[V_, D_, D_]],
        seed: int = 42,
    ) -> "NumPyGaussian[V_, D_]":
        return NumPyGaussian(
            mean=mean, covariance=covariance, rng=np.random.default_rng(seed)
        )

    def __post_init__(self) -> None:
        V, D = self.mean.shape

        assert shape_of(self.covariance, matches=(V, D, D)), (
            f"Covariance shape {self.covariance.shape} does not match mean shape {self.mean.shape}. "
            f"Expected covariance shape to be {(V, D, D)}, got {self.covariance.shape}."
        )

    def sample[N: int](self, count: N) -> NumPyUncertaintySamples[Dims[V, D], N]:
        V, D = self.mean.shape

        L = np.linalg.cholesky(self.covariance)
        z = self.rng.standard_normal(size=(V, D, count))

        samples = self.mean[..., None] + (L @ z)
        assert shape_of(samples, matches=(V, D, count), name="samples")

        return samples

    @property
    def shape(self) -> Dims[V, D]:
        return self.mean.shape


@dataclass(kw_only=True, frozen=True)
class NumPyUniform[ShapeT: Shape](NumPyUncertainty[ShapeT]):
    lower: Array[ShapeT]
    upper: Array[ShapeT]
    rng: np.random.Generator

    @staticmethod
    def create[S: Shape](
        *, lower: Array[S], upper: Array[S], seed: int = 42
    ) -> "NumPyUniform[S]":
        return NumPyUniform(lower=lower, upper=upper, rng=np.random.default_rng(seed))

    def __post_init__(self) -> None:
        lower_shape = self.lower.shape

        assert shape_of(self.upper, matches=lower_shape), (
            f"Upper bound shape {self.upper.shape} does not match lower bound shape {self.lower.shape}. "
            f"Expected upper bound shape to be {lower_shape}, got {self.upper.shape}."
        )
        assert np.all(self.upper >= self.lower), (
            "All upper bounds must be greater than lower bounds."
        )

    def sample[N: int](self, count: N) -> NumPyUncertaintySamples[ShapeT, N]:
        samples = roll_axes_left(
            self.rng.uniform(
                low=self.lower,
                high=self.upper,
                size=(count, *(shape := self.lower.shape)),
            )
        )

        assert shape_of(samples, matches=(*shape, count), name="samples")

        return cast(NumPyUncertaintySamples[ShapeT, N], samples)

    @property
    def shape(self) -> ShapeT:
        return self.lower.shape


def roll_axes_left(array: Array) -> Array:
    rest = array.shape[1:]
    return array.transpose(*range(1, len(rest) + 1), 0)
