from typing import Protocol, NamedTuple, Self, Annotated, Any, cast, overload
from types import TracebackType

from riskit.type import jaxtyped

from jax import Array as JaxArray
from jaxtyping import Float
from numtypes import Shape, AnyShape

import jax.numpy as jnp


class JaxBackend:
    @staticmethod
    def create() -> "JaxBackend":
        return JaxBackend()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        pass

    @jaxtyped
    @staticmethod
    def array_of(costs: "JaxCosts") -> "JaxCosts":
        return costs

    @overload
    @staticmethod
    def to_risk(array: Float[JaxArray, "T M"]) -> "JaxRisk": ...

    @overload
    @staticmethod
    def to_risk(array: Float[JaxArray, "M"], *, time_steps: int) -> "JaxRisk": ...

    @jaxtyped
    @staticmethod
    def to_risk(
        array: Float[JaxArray, "T M"] | Float[JaxArray, "M"],
        *,
        time_steps: int | None = None,
    ) -> "JaxRisk":
        match array.shape:
            case (M,):
                assert time_steps is not None, (
                    f"Received array of shape ({M},). You must specify the number of time steps "
                    "the risk should be padded to."
                )
                return jnp.broadcast_to(array / time_steps, (time_steps, M))

            case (T, M):
                assert time_steps is None, (
                    f"Received array of shape ({T}, {M}). Do not specify time_steps in this case."
                )
                return array
            case _:
                assert False, f"Unexpected array shape {array.shape} for risk."

    @jaxtyped
    @staticmethod
    def mean(data: Float[JaxArray, "..."], *, axis: int) -> Float[JaxArray, "..."]:
        return jnp.mean(data, axis=axis)

    @jaxtyped
    @staticmethod
    def var(data: Float[JaxArray, "..."], *, axis: int) -> Float[JaxArray, "..."]:
        return jnp.var(data, axis=axis)

    @jaxtyped
    @staticmethod
    def sum(data: Float[JaxArray, "..."], *, axis: int) -> Float[JaxArray, "..."]:
        return jnp.sum(data, axis=axis)

    @jaxtyped
    @staticmethod
    def axpby(
        *,
        a: float = 1.0,
        x: Float[JaxArray, "*S"],
        b: float = 1.0,
        y: Float[JaxArray, "*S"],
    ) -> Float[JaxArray, "*S"]:
        return a * x + b * y


type JaxInputs[T: int = Any, D_u: int = Any, M: int = Any] = Float[JaxArray, "T D_u M"]
"""Batch of control inputs. The dimensions are (time steps, control dimensions, trajectories)."""

type JaxStates[T: int = Any, D_x: int = Any, M: int = Any] = Float[JaxArray, "T D_x M"]
"""Batch of states. The dimensions are (time steps, state dimensions, trajectories)."""

type JaxUncertaintySamples[ShapeT: Shape = AnyShape, N: int = Any] = Float[
    JaxArray, "*S N"
]
"""Batch of uncertainty samples. The dimensions are (...uncertainty dimensions, uncertainty samples)."""

type JaxCosts[T: int = Any, M: int = Any, N: int = Any] = Annotated[
    Float[JaxArray, "T M N"], JaxBackend.create
]
"""Batch of costs. The dimensions are (time steps, trajectories, uncertainty samples)."""

type JaxRisk[T: int = Any, M: int = Any] = Float[JaxArray, "T M"]
"""Batch of risk values. The dimensions are (time steps, trajectories)."""


class JaxUncertainty[ShapeT: Shape](Protocol):
    def sample[N: int](self, count: N) -> JaxUncertaintySamples[ShapeT, N]:
        """Returns samples from the distribution of the uncertain variable(s)."""
        ...


class JaxBatchCostFunction[TrajectoriesT, UncertaintySamplesT](Protocol):
    def __call__(
        self, *, trajectories: TrajectoriesT, uncertainties: UncertaintySamplesT
    ) -> JaxCosts:
        """Describes the cost function that should be used for evaluating risk."""
        ...


class JaxInputAndState[T: int, D_u: int, D_x: int, M: int](NamedTuple):
    u: JaxInputs[T, D_u, M]
    x: JaxStates[T, D_x, M]

    def get(self) -> Self:
        return self

    @property
    def time_steps(self) -> T:
        return cast(T, self.u.shape[0])

    @property
    def trajectory_count(self) -> M:
        return cast(M, self.u.shape[2])
