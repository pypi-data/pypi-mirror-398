from dataclasses import dataclass

from riskit.risk import Uncertainties, SamplingResult


@dataclass(frozen=True)
class MonteCarlo[UncertaintySamplesT]:
    sample_count: int

    def sample_from(
        self, uncertainties: Uncertainties[UncertaintySamplesT]
    ) -> SamplingResult[UncertaintySamplesT]:
        return SamplingResult(
            samples=uncertainties.sample(count=self.sample_count),
            sample_count=self.sample_count,
        )


class sampler:
    @staticmethod
    def monte_carlo(sample_count: int = 5000) -> MonteCarlo:
        """Creates a Monte Carlo sampler with the specified sample count."""
        return MonteCarlo(sample_count=sample_count)
