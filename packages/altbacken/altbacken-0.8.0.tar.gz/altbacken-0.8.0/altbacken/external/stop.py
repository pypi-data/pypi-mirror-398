from datetime import timedelta, datetime

from altbacken.core.annealing import AnnealingState


class TemperatureThreshold:
    """
    Represents a temperature threshold for an annealing process.

    This class is used to determine whether a given annealing state's
    temperature has fallen below a specified threshold. It helps in controlling
    the termination criteria for algorithms based on simulated annealing
    techniques.

    Attributes:
        threshold (float): Specifies the non-negative temperature value used
            as the limit for comparison.
    """
    def __init__(self, threshold: float):
        if threshold < 0:
            raise ValueError("Threshold must be non-negative")
        self.threshold = threshold

    def __call__(self, state: AnnealingState) -> bool:
        return state.temperature < self.threshold

    def __str__(self) -> str:
        return f"Temperature less than {self.threshold}"

class IterationThreshold:
    """Represents a stopping criterion based on a threshold iteration count.

    This class is used to determine whether a process, such as an optimization
    algorithm, should stop based on the current iteration surpassing a predefined
    iteration threshold. It can be utilized as a callable object in these scenarios.

    Attributes:
        threshold (int): The iteration count threshold. The process stops
            when the current iteration reaches or exceeds this value.
    """
    def __init__(self, threshold: int):
        if threshold <= 0:
            raise ValueError("Threshold must be positive")
        self.threshold = threshold

    def __call__(self, state: AnnealingState) -> bool:
        return state.iteration >= self.threshold

    def __str__(self) -> str:
        return f"At most {self.threshold} iterations"


class SolutionImprovementThreshold:
    """
    Monitors the solution improvement status during an optimization process.

    This class is designed to track whether a predefined threshold of iterations
    without solution improvement is met. It can be used in annealing or other
    iterative optimization algorithms to determine when to terminate the process
    if sufficient improvement is not observed.

    Attributes:
        max_iterations_without_improvement (int): Maximum number of iterations
            allowed without any improvement in the solution before termination.
    """
    def __init__(self, max_iterations_without_improvement: int):
        if max_iterations_without_improvement <= 0:
            raise ValueError("Maximum iterations without improvement must be positive")
        self._max_iterations_without_improvement: int = max_iterations_without_improvement
        self._last_improvement_iteration: int = 0
        self._last_best_value: float = float("inf")

    def __call__(self, state: AnnealingState) -> bool:
        if state.iteration == 0:
            self._last_best_value = float("inf")
            self._last_improvement_iteration = 0
        if state.best_solution < self._last_best_value:
            self._last_best_value = state.best_value
            self._last_improvement_iteration = state.iteration
        return state.iteration - self._last_improvement_iteration >= self._max_iterations_without_improvement


class TimeThreshold:
    """
    Represents a time-based threshold for tracking the progress of an annealing process.

    This class is used to determine whether a given amount of time has passed since the
    start of the annealing process.
    """
    def __init__(self, threshold: timedelta | float):
        """
        Initializes the timer with a specified threshold and sets an end time based on this threshold.

        Args:
            threshold (timedelta | float): Time duration for the threshold. If a float is provided, it is interpreted
                as seconds. It must be positive.

        Raises:
            ValueError: If the given threshold is less than or equal to zero.
        """
        self._threshold: timedelta = threshold if isinstance(threshold, timedelta) else timedelta(seconds=threshold)
        if self._threshold.total_seconds() <= 0:
            raise ValueError("Threshold must be positive")
        self._end: datetime = datetime.now() + self._threshold

    @property
    def threshold(self) -> timedelta:
        """
        Provides access to the threshold value as a read-only property.

        Returns:
            timedelta: The threshold value.
        """
        return self._threshold

    def __call__(self, state: AnnealingState) -> bool:
        """
        Determines whether the annealing process should be terminated based on the
        current iteration or elapsed time.

        This callable method evaluates two conditions. It resets the timer if the
        current iteration is the initial one (iteration 0) and ensures the optimization
        process continues. For all subsequent iterations, it checks if the current
        time has reached or surpassed the predetermined end time, determining if the
        termination condition has been met.

        Args:
            state (AnnealingState): The current state of the annealing process,
                including its iteration count and other relevant details.

        Returns:
            bool: True if the termination condition is satisfied, otherwise False.
        """
        if state.iteration == 0:
            self._reset_timer()
            return False
        else:
            return datetime.now() >= self._end

    def _reset_timer(self):
        self._end = datetime.now() + self._threshold