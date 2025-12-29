from collections.abc import Callable
from typing import Literal, cast

from altbacken.core.annealing import AnnealingState
from altbacken.internal.analysis.base import AnalysisResult


def _absolute(last: float, current: float) -> float:
    return abs(current - last)

def _relative(last: float, current: float) -> float:
    try:
        return abs(current -last) / abs(last)
    except ZeroDivisionError:
        return 0.0

class ConvergenceAnalyzer[T]:
    """Analyzer for detecting convergence in simulated annealing simulations."""

    def __init__(self, method: Literal["relative", "absolute"] = "relative"):
        self._fitness_value: float = float("inf")
        self._method: Literal["relative", "absolute"] = method
        self._op: Callable[[float, float], float] = _relative if method == "relative" else _absolute

    def __call__(self, state: AnnealingState[T]) -> AnalysisResult | None:
        """Analyze the given state and return convergence metrics."""
        if state.iteration == 0:
            self._fitness_value = state.current_value
            return None
        convergence: float = self._op(self._fitness_value, state.current_value)
        self._fitness_value = state.current_value
        return cast(
            AnalysisResult,
            {
                "topic": "convergence",
                "value": convergence,
                "iteration": state.iteration,
                "method": cast(str, self._method)
            }
        )
