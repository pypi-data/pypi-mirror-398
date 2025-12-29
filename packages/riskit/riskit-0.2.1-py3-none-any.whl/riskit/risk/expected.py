from dataclasses import dataclass

from riskit.risk.common import (
    Costs,
    Risk,
    ArrayLike,
    BatchCostFunction,
    TrajectoriesProvider,
    Uncertainties,
    Backend,
    Sampler,
)


@dataclass(frozen=True)
class ExpectedValue[
    TrajectoriesT,
    UncertaintySamplesT,
    CostsT: Costs,
    RiskT: Risk,
    ArrayT: ArrayLike,
]:
    cost: BatchCostFunction[TrajectoriesT, UncertaintySamplesT, CostsT]
    backend: Backend[CostsT, RiskT, ArrayT]
    sampler: Sampler[UncertaintySamplesT]

    def compute(
        self,
        *,
        trajectories: TrajectoriesProvider[TrajectoriesT],
        uncertainties: Uncertainties[UncertaintySamplesT],
    ) -> RiskT:
        T, M = trajectories.time_steps, trajectories.trajectory_count

        samples, N = self.sampler.sample_from(uncertainties)
        costs = self.cost(trajectories=trajectories.get(), uncertainties=samples)

        assert costs.shape == (T, M, N), (
            f"Costs shape {costs.shape} does not match expected shape {(T, M, N)}."
        )

        with self.backend as op:
            return op.to_risk(op.mean(op.array_of(costs), axis=2))

    def sampled_with(
        self, sampler: Sampler[UncertaintySamplesT]
    ) -> "ExpectedValue[TrajectoriesT, UncertaintySamplesT, CostsT, RiskT, ArrayT]":
        return ExpectedValue(cost=self.cost, backend=self.backend, sampler=sampler)
