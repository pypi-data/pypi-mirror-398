from dataclasses import dataclass

from riskit.risk.common import (
    Costs,
    Risk,
    ArrayLike,
    BatchCostFunction,
    TrajectoriesProvider,
    Uncertainties,
    Sampler,
    Backend,
)


@dataclass(frozen=True)
class MeanVariance[
    TrajectoriesT,
    UncertaintySamplesT,
    CostsT: Costs,
    RiskT: Risk,
    ArrayT: ArrayLike,
]:
    cost: BatchCostFunction[TrajectoriesT, UncertaintySamplesT, CostsT]
    backend: Backend[CostsT, RiskT, ArrayT]
    sampler: Sampler[UncertaintySamplesT]
    gamma: float

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
            costs = op.sum(op.array_of(costs), axis=0)
            mean, variance = op.mean(costs, axis=1), op.var(costs, axis=1)

            return op.to_risk(op.axpby(x=mean, b=self.gamma, y=variance), time_steps=T)

    def sampled_with(
        self, sampler: Sampler[UncertaintySamplesT]
    ) -> "MeanVariance[TrajectoriesT, UncertaintySamplesT, CostsT, RiskT, ArrayT]":
        return MeanVariance(
            cost=self.cost, backend=self.backend, sampler=sampler, gamma=self.gamma
        )
