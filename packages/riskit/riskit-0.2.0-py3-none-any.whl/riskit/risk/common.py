from typing import Any, Protocol, NamedTuple, overload
from types import TracebackType

from numtypes import Shape, Dims, Array


class ArrayLike[ShapeT: Shape](Protocol):
    def __array__(self) -> Array[ShapeT]:
        """Converts the object to a NumPy array with the given shape."""
        ...

    @property
    def shape(self) -> ShapeT | tuple[int, ...]:
        """Shape of the array like object."""
        ...


type Costs[T: int = Any, M: int = Any, N: int = Any] = ArrayLike[Dims[T, M, N]]
"""A costs array of shape (time steps, trajectories, uncertainty samples)."""

type Risk[T: int = Any, M: int = Any] = ArrayLike[Dims[T, M]]
"""A risk array of shape (time steps, trajectories)."""


class BatchCostFunction[TrajectoriesT, UncertaintySamplesT, CostsT: Costs](Protocol):
    def __call__(
        self, *, trajectories: TrajectoriesT, uncertainties: UncertaintySamplesT
    ) -> CostsT:
        """Describes the cost function that should be used for evaluating risk.

        Returns:
            An array like object of shape (M, N) where M is the number of trajectories
            and N is the number of uncertainty samples.
        """
        ...


class TrajectoriesProvider[TrajectoriesT](Protocol):
    def get(self) -> TrajectoriesT:
        """Provides the batch of trajectories for which the risk metric should be computed."""
        ...

    @property
    def time_steps(self) -> int:
        """Number of time steps in the provided trajectories."""
        ...

    @property
    def trajectory_count(self) -> int:
        """Number of trajectories provided."""
        ...


class Uncertainties[UncertaintySamplesT](Protocol):
    def sample(self, count: int) -> UncertaintySamplesT:
        """Returns samples from the distribution(s) of the uncertain variable(s)."""
        ...


class Computation[CostsT: Costs, RiskT: Risk, ArrayT: ArrayLike](Protocol):
    def array_of(self, costs: CostsT) -> ArrayT:
        """Converts the given costs to the backend's array type."""
        ...

    @overload
    def to_risk(self, array: ArrayT) -> RiskT:
        """Converts the given array to the backend's risk type."""
        ...

    @overload
    def to_risk(self, array: ArrayT, *, time_steps: int) -> RiskT:
        """Converts the given array to the backend's risk type.

        Note:
            It is assumed that the provided array has dimensions (trajectories,). Thus, the
            risk values will be shared equally across all time steps to generate a risk of
            shape (time steps, trajectories).
        """
        ...

    def sum(self, data: ArrayT, *, axis: int) -> ArrayT:
        """Computes the sum of the given data along the specified axis."""
        ...

    def mean(self, data: ArrayT, *, axis: int) -> ArrayT:
        """Computes the mean of the given data along the specified axis."""
        ...

    def var(self, data: ArrayT, *, axis: int) -> ArrayT:
        """Computes the variance of the given data along the specified axis."""
        ...

    def axpby(self, *, a: float = 1.0, x: ArrayT, b: float = 1.0, y: ArrayT) -> ArrayT:
        """Computes the operation a * x + b * y."""
        ...


class Backend[CostsT: Costs, RiskT: Risk, ArrayT: ArrayLike](Protocol):
    def __enter__(self) -> Computation[CostsT, RiskT, ArrayT]:
        """Enters the backend context for computations."""
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Exits the backend context."""
        ...


class SamplingResult[UncertaintySamplesT](NamedTuple):
    samples: UncertaintySamplesT
    sample_count: int


class Sampler[UncertaintySamplesT](Protocol):
    def sample_from(
        self, uncertainties: Uncertainties[UncertaintySamplesT]
    ) -> SamplingResult[UncertaintySamplesT]:
        """Samples from the given uncertainties."""
        ...


class RiskMetric[TrajectoriesT, UncertaintySamplesT, RiskT: Risk](Protocol):
    def compute(
        self,
        *,
        trajectories: TrajectoriesProvider[TrajectoriesT],
        uncertainties: Uncertainties[UncertaintySamplesT],
    ) -> RiskT:
        """Computes the risk metric for the given trajectories and uncertainties.

        Returns:
            An array like object of shape (trajectories,) representing the risk
            values for each trajectory.
        """
        ...

    def sampled_with(
        self, sampler: Sampler[UncertaintySamplesT]
    ) -> "RiskMetric[TrajectoriesT, UncertaintySamplesT, RiskT]":
        """Returns a new risk metric that uses the given sampler to sample from uncertainties."""
        ...
