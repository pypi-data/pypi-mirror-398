from collections.abc import Iterable
from random import random as builtin_random

from altbacken.core.annealing import SimulatedAnnealing, FitnessFunction, TemperatureFunction, StopCondition, \
    AcceptanceFunction, RandomNumberGenerator
from altbacken.core.neighbourhood import Neighbourhood
from altbacken.external.acceptance import BoltzmannAcceptance
from altbacken.external.stop import IterationThreshold, TemperatureThreshold
from altbacken.external.temperature import PredefinedTemperature, ExponentialCooling


class SimpleSimulatedAnnealing[T](SimulatedAnnealing[T]):
    """
    This class implements a simple simulated annealing optimization algorithm.

    SimpleSimulatedAnnealing extends the functionality of the `SimulatedAnnealing`
    class, providing a simplified interface and additional features for configuring
    the temperature and stopping conditions. It supports various temperature and
    stopping condition configurations for enhanced adaptability and performance.

    Attributes:
        fitness (FitnessFunction[T]): The fitness function used for evaluating the
            quality of solutions.
        neighbourhood (Neighbourhood[T]): The neighbourhood function that defines
            possible moves in the solution space.
        temperature (Iterable[float] | float | tuple[float, float] |
            TemperatureFunction): Initial temperature configuration for simulated
            annealing. Can be a float, tuple, iterable, or a temperature function.
        stop (int | float | StopCondition[T]): Stopping condition for the algorithm.
            Can be an integer for iteration threshold, a float for temperature
            threshold, or a custom stop condition.
        acceptance (AcceptanceFunction): Acceptance function used to calculate the energy difference
            between states. Defaults to `BoltzmannAcceptance`.
        random (RandomNumberGenerator): Random number generator used in the algorithm.
            Defaults to `builtin_random`.
    """
    def __init__(
            self,
            fitness: FitnessFunction[T],
            neighbourhood: Neighbourhood[T],
            temperature: Iterable[float] | float | tuple[float, float] | TemperatureFunction[T] = 1000.0,
            stop: int | float | StopCondition[T] = 1000,
            acceptance: AcceptanceFunction = BoltzmannAcceptance(),
            random: RandomNumberGenerator = builtin_random

    ):
        super().__init__(
            fitness,
            self._parse_temperature(temperature),
            neighbourhood,
            self._parse_stop(stop),
            acceptance,
            random
        )

    @classmethod
    def _parse_stop(cls, stop: int | float | StopCondition[T]) -> StopCondition[T]:
        match stop:
            case int(): return IterationThreshold(stop)
            case float(): return TemperatureThreshold(stop)
            case other: return other

    @classmethod
    def _parse_temperature(
            cls,
            temperature: Iterable[float] | float | tuple[float, float] | TemperatureFunction
    ) -> TemperatureFunction:
        match temperature:
            case[start, cooling_rate]: return ExponentialCooling(start, cooling_rate)
            case Iterable(): return PredefinedTemperature(temperature)
            case float(temperature): return ExponentialCooling(temperature)
            case other: return other
