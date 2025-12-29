from typing import Any, Protocol, NamedTuple, Self, Annotated, overload
from types import TracebackType

from numtypes import Array, Dims, Shape, AnyShape, shape_of

import numpy as np


class NumPyBackend:
    @staticmethod
    def create() -> "NumPyBackend":
        return NumPyBackend()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        pass

    def array_of(self, costs: "NumPyCosts") -> "NumPyCosts":
        return costs

    @overload
    def to_risk[T: int, M: int](
        self, array: Array[Dims[T, M]]
    ) -> "NumPyRisk[T, M]": ...

    @overload
    def to_risk[T: int, M: int](
        self, array: Array[Dims[M]], *, time_steps: T
    ) -> "NumPyRisk[T, M]": ...

    def to_risk[T: int, M: int](
        self,
        array: Array[Dims[T, M]] | Array[Dims[M]],
        *,
        time_steps: T | None = None,
    ) -> "NumPyRisk[T, M]":
        match array.shape:
            case (M,):
                assert time_steps is not None, (
                    f"Received array of shape ({M},). You must specify the number of time steps "
                    "the risk should be padded to."
                )

                risk = np.full((time_steps, M), array / time_steps)

                assert shape_of(risk, matches=(time_steps, M), name="risk")

                return risk

            case (T, M):
                assert time_steps is None, (
                    f"Received array of shape ({T}, {M}). Do not specify time_steps in this case."
                )
                assert shape_of(array, matches=(T, M), name="risk")
                return array

    def mean(self, data: Array, *, axis: int) -> Array:
        return np.mean(data, axis=axis)

    def var(self, data: Array, *, axis: int) -> Array:
        return np.var(data, axis=axis)

    def sum(self, data: Array, *, axis: int) -> Array:
        return np.sum(data, axis=axis)

    def axpby[S: Shape](
        self, *, a: float = 1.0, x: Array[S], b: float = 1.0, y: Array[S]
    ) -> Array[S]:
        result = a * x + b * y

        assert shape_of(result, matches=x.shape)

        return result


type NumPyInputs[T: int = Any, D_u: int = Any, M: int = Any] = Array[Dims[T, D_u, M]]
"""Batch of control inputs. The dimensions are (time steps, control dimensions, trajectories)."""

type NumPyStates[T: int = Any, D_x: int = Any, M: int = Any] = Array[Dims[T, D_x, M]]
"""Batch of states. The dimensions are (time steps, state dimensions, trajectories)."""

type NumPyUncertaintySamples[ShapeT: Shape = AnyShape, N: int = Any] = Array[
    Dims[*ShapeT, N]
]
"""Batch of uncertainty samples. The dimensions are (...uncertainty dimensions, uncertainty samples)."""

type NumPyCosts[T: int = Any, M: int = Any, N: int = Any] = Annotated[
    Array[Dims[T, M, N]], NumPyBackend.create
]
"""Batch of costs. The dimensions are (time steps, trajectories, uncertainty samples)."""

type NumPyRisk[T: int = Any, M: int = Any] = Array[Dims[T, M]]
"""Batch of risk values. The dimensions are (time steps, trajectories)."""


class NumPyUncertainty[ShapeT: Shape](Protocol):
    def sample[N: int](self, count: N) -> NumPyUncertaintySamples[ShapeT, N]:
        """Returns samples from the distribution of the uncertain variable(s)."""
        ...


class NumPyBatchCostFunction[TrajectoriesT, UncertaintySamplesT](Protocol):
    def __call__(
        self, *, trajectories: TrajectoriesT, uncertainties: UncertaintySamplesT
    ) -> NumPyCosts:
        """Describes the cost function that should be used for evaluating risk."""
        ...


class NumPyInputAndState[T: int, D_u: int, D_x: int, M: int](NamedTuple):
    u: NumPyInputs[T, D_u, M]
    x: NumPyStates[T, D_x, M]

    def get(self) -> Self:
        return self

    @property
    def time_steps(self) -> T:
        return self.u.shape[0]

    @property
    def trajectory_count(self) -> M:
        return self.u.shape[2]
