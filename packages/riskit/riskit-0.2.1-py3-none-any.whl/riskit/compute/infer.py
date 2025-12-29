from typing import Protocol

from riskit.risk import BatchCostFunction, Backend, Costs
from riskit.annotations import return_annotation_of


class BackendCreator[BackendT: Backend](Protocol):
    def __call__(self) -> BackendT:
        """Creates a backend instance for computations."""
        ...


class infer:
    @staticmethod
    def backend_from[
        TrajectoriesT,
        UncertaintySamplesT,
        CostsT: Costs,
        BackendT: Backend,
    ](
        function: BatchCostFunction[TrajectoriesT, UncertaintySamplesT, CostsT],
        *,
        type: type[BackendT],
    ) -> BackendT:
        return return_annotation_of(
            function, type=tuple[BackendCreator[BackendT]]
        ).metadata[0]()
