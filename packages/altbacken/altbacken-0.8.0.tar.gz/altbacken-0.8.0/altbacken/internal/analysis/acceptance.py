from typing import cast

from altbacken.core.annealing import AcceptanceFunction, AnnealingState
from altbacken.internal.analysis.base import AnalysisResult


class AcceptanceAnalyzer[T]:

    def __init__(self, energy: AcceptanceFunction, boltzmann_constant: float = 1.0):
        self._energy: AcceptanceFunction = energy
        self._boltzmann_constant: float = boltzmann_constant
        self._last_value: float = float("inf")

    def __call__(self, state: AnnealingState[T]) -> AnalysisResult | None:
        if state.iteration == 0:
            self._last_value = state.current_value
            return None
        else:
            energy: float = self._energy(self._last_value, state.current_value, self._boltzmann_constant)
            self._last_value = state.current_value
            return cast(
                AnalysisResult,
                {
                    "topic": "acceptance",
                    "value": energy,
                    "iteration": state.iteration,
                    "message": f"Acceptance: {energy:.2f}"
                }
            )