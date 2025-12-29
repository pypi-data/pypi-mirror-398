from collections.abc import Callable
from functools import wraps
from typing import Protocol
from random import random as builtin_random

from altbacken.core.neighbourhood import Neighbourhood
from altbacken.core.state import AnnealingState


class StopCondition[T](Protocol):
    """
    Protocol that defines a stop condition for an annealing process.

    This protocol is used to determine whether a simulated annealing process
    should terminate, based on the current state of the annealing procedure.
    Implementations of this protocol must define the __call__ method to evaluate
    the termination condition.

    Attributes:
        None
    """
    def __call__(self, state: AnnealingState[T]) -> bool:
        """
        Callable object to determine the termination condition of an annealing process.

        This function evaluates whether the annealing process should terminate upon
        being called with the current state. The decision logic is embedded within the
        function implementation, based on the properties and status of the provided
        current state.

        Args:
            state (AnnealingState[T]): The current state of the annealing process,
                providing the necessary information to evaluate the termination
                condition.

        Returns:
            bool: A boolean indicating whether the annealing process should terminate.
        """

type FitnessFunction[T] = Callable[[T], float]
type TemperatureFunction[T] = Callable[[AnnealingState[T]], float]
type AcceptanceFunction = Callable[[float, float, float], float]
type RandomNumberGenerator = Callable[[], float]
type RandomNumberRange = Callable[[int, int], int]
type Tracer[T] = Callable[[AnnealingState[T]], None]


def invert_fitness_function[T](fitness_function: FitnessFunction[T]) -> FitnessFunction[T]:
    """Inverts the sign of the fitness function, converting maximization to minimization or vice versa."""
    @wraps(fitness_function)
    def _wrapper(x: T) -> float:
        return -fitness_function(x)
    _wrapper.__name__ = f'inverted_{fitness_function.__name__}'
    return _wrapper


def _no_trace[T](_: AnnealingState[T]) -> None:
    """A no-op tracer function that does not perform any tracing."""
    pass

class SimulatedAnnealing[T]:
    """
    SimulatedAnnealing class represents the simulated annealing optimization algorithm.

    This class performs optimization based on the simulated annealing technique, which iteratively
    explores a solution space to find a globally optimal solution for a given problem. The process relies
    on various components, such as temperature scheduling, fitness evaluation, neighborhood exploration,
    stop conditions, and energy functions to simulate the annealing process for optimization problems.

    Attributes:
        fitness (FitnessFunction[T]): A function that evaluates the fitness of a solution.
        temperature (TemperatureFunction): A generator function that determines the temperature at each iteration.
        neighbourhood (Neighbourhood[T]): A function that generates a neighboring solution for the current solution.
        stop_condition (StopCondition[T]): A function that determines when to stop the annealing process.
        energy (EnergyFunction): A function that computes the probability of transitioning between solutions.
        random (RandomNumberGenerator): A random number generator function, defaults to a built-in generator.
    """
    def __init__(
            self,
            fitness: FitnessFunction[T],
            temperature: TemperatureFunction,
            neighbourhood: Neighbourhood[T],
            stop_condition: StopCondition[T],
            energy: AcceptanceFunction,
            random: RandomNumberGenerator = builtin_random
    ):
        self._fitness: FitnessFunction[T] = fitness
        self._temperature: TemperatureFunction[T] = temperature
        self._neighbourhood: Neighbourhood[T] = neighbourhood
        self._stop_condition: StopCondition[T] = stop_condition
        self._energy: AcceptanceFunction = energy
        self._random: RandomNumberGenerator = random
        self._tracer: Tracer[T] = _no_trace

    @property
    def tracer(self) -> Tracer[T]:
        return self._tracer

    @tracer.setter
    def tracer(self, tracer: Tracer[T]) -> None:
        self._tracer = tracer


    @property
    def energy(self) -> AcceptanceFunction:
        return self._energy


    def simulate(self, initial: T) -> tuple[T, float]:
        """
        Simulates an optimization process using a predefined algorithm.

        This method performs an iterative optimization process through a simulated
        annealing approach. A neighborhood function generates potential solutions,
        and fitness values are evaluated to determine solution quality. The process
        continues until a stopping condition is satisfied or a temperature generator
        is exhausted.

        Args:
            initial (T): The initial solution to start the optimization process.

        Returns:
            tuple[T, float]: A tuple containing the best solution found and its
            corresponding fitness value.

        Raises:
            StopIteration: If the temperature generator is exhausted before meeting
            the stopping condition.
        """
        initial_value: float = self._fitness(initial)
        state: AnnealingState[T] = AnnealingState(0, 0.0, initial, initial_value, initial, initial_value)
        state.temperature = self._temperature(state)
        while not self._stop_condition(state):
            x: T = self._neighbourhood(state)
            y: float = self._fitness(x)
            state.improvement = False
            if y < state.best_value:
                state.best_value = y
                state.best_solution = x
                state.current_value = y
                state.current_solution = x
                state.improvement = True
            elif self._phase_out(state.best_value, y, state.temperature):
                state.current_value = y
                state.current_solution = x
            self._tracer(state)
            state.iteration += 1
            state.temperature = self._temperature(state)
        return state.best_solution, state.best_value

    def _phase_out(self, current_value: float, new_value: float, current_temperature: float) -> bool:
        return self._random() < self._energy(current_value, new_value, current_temperature)