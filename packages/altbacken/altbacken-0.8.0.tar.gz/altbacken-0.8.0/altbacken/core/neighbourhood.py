from collections.abc import Callable
from typing import Protocol

from altbacken.core.state import AnnealingState


type TemperatureScaling = Callable[[float], float]


def no_temperature_scaling(_: float) -> float:
    return 1.0


class Neighbourhood[T](Protocol):
    """
    Represents a neighbourhood protocol for defining neighbours of a data point.

    Attributes:
        None.
    """
    def __call__(self, state: AnnealingState[T]) -> T:
        """
        Applies the callable object to the given state and returns the result.

        This method allows instances of the class to be called as functions. It
        processes the provided AnnealingState and produces a result based
        on the intended functionality defined in the implementation.

        Args:
            state: The annealing state object containing the current state
                and associated data for processing.

        Returns:
            The result of processing the provided annealing state.
        """