from typing import overload

from riskit.risk import (
    BatchCostFunction,
    Backend,
    RiskMetric,
    Risk,
    Costs,
    ArrayLike,
    ExpectedValue,
    MeanVariance,
)
from riskit.compute import (
    infer,
    NumPyBatchCostFunction,
    NumPyRisk,
    JaxBatchCostFunction,
    JaxRisk,
)
from riskit.sampler import sampler


class risk:
    @overload
    @staticmethod
    def expected_value_of[TrajectoriesT, UncertaintySamplesT](
        function: NumPyBatchCostFunction[TrajectoriesT, UncertaintySamplesT],
    ) -> RiskMetric[TrajectoriesT, UncertaintySamplesT, NumPyRisk]:
        """Creates an Expected Value risk metric using the NumPy backend."""
        ...

    @overload
    @staticmethod
    def expected_value_of[TrajectoriesT, UncertaintySamplesT](
        function: JaxBatchCostFunction[TrajectoriesT, UncertaintySamplesT],
    ) -> RiskMetric[TrajectoriesT, UncertaintySamplesT, JaxRisk]:
        """Creates an Expected Value risk metric using the JAX backend."""
        ...

    @overload
    @staticmethod
    def expected_value_of[
        TrajectoriesT,
        UncertaintySamplesT,
        CostsT: Costs,
        RiskT: Risk,
        ArrayT: ArrayLike,
    ](
        function: BatchCostFunction[TrajectoriesT, UncertaintySamplesT, CostsT],
        backend: Backend[CostsT, RiskT, ArrayT],
    ) -> RiskMetric[TrajectoriesT, UncertaintySamplesT, RiskT]:
        """Creates an Expected Value risk metric using the specified backend."""
        ...

    @staticmethod
    def expected_value_of[  # type: ignore
        TrajectoriesT,
        UncertaintySamplesT,
        CostsT: Costs,
        RiskT: Risk,
        ArrayT: ArrayLike,
    ](
        function: BatchCostFunction[TrajectoriesT, UncertaintySamplesT, CostsT],
        backend: Backend[CostsT, RiskT, ArrayT] | None = None,
    ) -> RiskMetric[TrajectoriesT, UncertaintySamplesT, RiskT]:
        return ExpectedValue(
            cost=function,
            backend=backend
            or infer.backend_from(function, type=Backend[CostsT, RiskT, ArrayT]),
            sampler=sampler.monte_carlo(),
        )

    @overload
    @staticmethod
    def mean_variance_of[TrajectoriesT, UncertaintySamplesT](
        function: NumPyBatchCostFunction[TrajectoriesT, UncertaintySamplesT],
        *,
        gamma: float,
    ) -> RiskMetric[TrajectoriesT, UncertaintySamplesT, NumPyRisk]:
        """Creates a Mean-Variance risk metric using the NumPy backend."""
        ...

    @overload
    @staticmethod
    def mean_variance_of[TrajectoriesT, UncertaintySamplesT](
        function: JaxBatchCostFunction[TrajectoriesT, UncertaintySamplesT],
        *,
        gamma: float,
    ) -> RiskMetric[TrajectoriesT, UncertaintySamplesT, JaxRisk]:
        """Creates a Mean-Variance risk metric using the JAX backend."""
        ...

    @overload
    @staticmethod
    def mean_variance_of[
        TrajectoriesT,
        UncertaintySamplesT,
        CostsT: Costs,
        RiskT: Risk,
        ArrayT: ArrayLike,
    ](
        function: BatchCostFunction[TrajectoriesT, UncertaintySamplesT, CostsT],
        *,
        backend: Backend[CostsT, RiskT, ArrayT],
        gamma: float,
    ) -> RiskMetric[TrajectoriesT, UncertaintySamplesT, RiskT]:
        """Creates a Mean-Variance risk metric using the specified backend."""
        ...

    @staticmethod
    def mean_variance_of[
        TrajectoriesT,
        UncertaintySamplesT,
        CostsT: Costs,
        RiskT: Risk,
        ArrayT: ArrayLike,
    ](
        function: BatchCostFunction[TrajectoriesT, UncertaintySamplesT, CostsT],
        *,
        backend: Backend[CostsT, RiskT, ArrayT] | None = None,
        gamma: float,
    ) -> RiskMetric[TrajectoriesT, UncertaintySamplesT, RiskT]:
        return MeanVariance(
            cost=function,
            backend=backend
            or infer.backend_from(function, type=Backend[CostsT, RiskT, ArrayT]),
            sampler=sampler.monte_carlo(),
            gamma=gamma,
        )
