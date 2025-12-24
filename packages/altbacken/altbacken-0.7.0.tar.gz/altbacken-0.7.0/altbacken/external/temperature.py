from collections.abc import Iterable, Sequence
from math import log
from typing import Any

from altbacken.core.annealing import AnnealingState


class PredefinedTemperature:
    """
    Represents a predefined sequence of temperature values.

    This class allows storing a predefined series of temperatures and provides
    functionality to iterate over these temperatures in a generator-like fashion.
    It ensures the sequence is not empty upon instantiation.

    Attributes:
        temperature (Sequence[float]): Immutable sequence of predefined
            temperature values.
    """
    def __init__(self, temperature: Iterable[float]):
        self._temperature: Sequence[float] = tuple(temperature)
        if not self._temperature:
            raise ValueError("Temperature sequence must not be empty")

    def __call__(self, state: AnnealingState[Any]) -> float:
        if state.iteration >= len(self._temperature):
            return 0.0
        else:
            return self._temperature[state.iteration]


class ExponentialCooling:
    """
    Handles exponential cooling calculations.

    This class provides functionality for simulating exponential cooling.
    It calculates decreasing temperature values based on an initial
    temperature and a specified cooling rate. The `ExponentialCooling`
    class can be used in optimization problems such as simulated annealing.

    Attributes:
        initial_temperature (float): The starting temperature for the
            cooling process.
        cooling_rate (float): The rate at which the temperature decreases
            in each step. It must be a value in the range (0, 1).
    """
    def __init__(self, initial_temperature: float, cooling_rate: float = 0.9):
        if initial_temperature <= 0:
            raise ValueError("Initial temperature must be positive")
        if cooling_rate <= 0 or cooling_rate >= 1:
            raise ValueError("Cooling rate must be in (0, 1)")
        self._initial_temperature = initial_temperature
        self._cooling_rate = cooling_rate

    def __call__(self, state: AnnealingState[Any]) -> float:
        return self._initial_temperature * (self._cooling_rate ** state.iteration)


class LogarithmicCooling:
    """
    Implements a logarithmic cooling schedule generator.

    The class provides a cooling schedule based on a logarithmic function. It is
    used commonly in simulated annealing or other optimization algorithms to
    introduce a gradually decreasing parameter (like temperature). The
    logarithmic cooling ensures a steady and slow decrease in the temperature
    value over iterations, making it suitable for problems requiring fine-tuning
    during optimization.

    Attributes:
        initial_temperature (float): The starting temperature value for the cooling
            schedule.
        shift (float): A shift factor added to the logarithm denominator to avoid
            division errors and regulate the cooling rate.
    """
    def __init__(self, initial_temperature: float, shift: float = 1.1):
        if shift <= 1:
            raise ValueError("Shift must be greater than 1")
        if initial_temperature <= 0:
            raise ValueError("Initial temperature must be positive")
        self._initial_temperature: float = initial_temperature
        self._shift: float = shift

    def __call__(self, state: AnnealingState[Any]) -> float:
        return self._initial_temperature / log(state.iteration + self._shift)


class LinearCooling:
    def __init__(self, initial_temperature: float, step: float):
        if step <= 0:
            raise ValueError("Step must be positive")
        if initial_temperature <= 0:
            raise ValueError("Initial temperature must be positive")
        self._initial_temperature: float = initial_temperature
        self._step: float = step

    def __call__(self, state: AnnealingState[Any]) -> float:
        return max(self._initial_temperature - state.iteration * self._step, 0)


class AdaptiveCooling:
    """
    Represents a cooling schedule with adaptive adjustments based on the state of the annealing process.

    This class implements a cooling mechanism for simulated annealing, where the temperature
    adapts based on the progress and quality of the current state. The temperature either decreases
    or slightly increases, aiming to balance exploration and exploitation during the optimization process.

    Attributes:
        initial_temperature (float): Initial temperature to start the annealing process.
        cooling (float): Factor to decrement the temperature when the current value is not optimal.
        heating (float): Factor to increment the temperature slightly to allow further exploration when
            the current value matches the best value.
    """
    def __init__(self, initial_temperature: float, cooling: float = 0.9, heating: float = 1.1):
        if cooling >= 1.0 or cooling <= 0:
            raise ValueError("Cooling factor must be less than 1 and positive")
        if heating <= 1.0:
            raise ValueError("Heating factor must be greater than 1")
        if initial_temperature <= 0:
            raise ValueError("Initial temperature must be positive")
        self._initial_temperature: float = initial_temperature
        self._cooling: float = cooling
        self._heating: float = heating

    def __call__(self, state: AnnealingState[Any]) -> float:
        if state.iteration == 0:
            return self._initial_temperature
        return state.temperature * self._heating if state.improvement else state.temperature * self._cooling
