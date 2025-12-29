from dataclasses import dataclass


@dataclass
class AnnealingState[T]:
    """
    Represents the state of the simulated annealing process.

    This class contains information about the current state of the process,
    including details about the iteration, temperature, and solutions
    (both current and best). It is designed to encapsulate and track the
    progress of the annealing algorithm, allowing for monitoring and analysis.

    Attributes:
        iteration (int): The current iteration number of the annealing process.
        temperature (float): The current temperature in the annealing schedule.
        current_solution (T): The solution being evaluated at the current step.
        current_value (float): The evaluation value of the current solution.
        best_solution (T): The best solution found so far.
        best_value (float): The evaluation value of the best solution found so far.
        improvement (bool): A flag indicating whether the current solution is better than the best solution found so far.
    """
    iteration: int
    temperature: float
    current_solution: T
    current_value: float
    best_solution: T
    best_value: float
    improvement: bool = False

    @classmethod
    def initial(cls, initial_solution: T, initial_value: float, temperature: float = 0.0) -> 'AnnealingState[T]':
        return cls(0, temperature, initial_solution, initial_value, initial_solution, initial_value)