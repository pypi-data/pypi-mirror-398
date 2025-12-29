from collections.abc import Sequence, Callable, Iterable
from random import random as builtin_random
from typing import Protocol, Self

from altbacken.core.annealing import RandomNumberGenerator, AnnealingState
from altbacken.core.neighbourhood import no_temperature_scaling, TemperatureScaling


class VectorNeighbourhood:
    """
    Defines a class for generating a neighborhood of vectors.

    The VectorNeighbourhood class generates new vectors by applying a small
    random perturbation to each component of an input vector.

    Attributes:
        epsilon (float): Magnitude of the perturbation applied to the input
            vector during neighborhood generation.
        random (RandomNumberGenerator): Random number generator used for
            creating perturbations.
        vector_type (Callable[[Iterable[float]], Sequence[float]]): Function
            used to define the type or structure of the output vector.
    """
    def __init__(
            self,
            epsilon: float = 0.1,
            random: RandomNumberGenerator = builtin_random,
            vector_type: Callable[[Iterable[float]], Sequence[float]] = tuple,
            temperature_scaling: TemperatureScaling = no_temperature_scaling
    ):
        self._epsilon: float = epsilon
        self._random: RandomNumberGenerator = random
        self._vector_type: Callable[[Iterable[float]], Sequence[float]] = vector_type
        self._temperature_scaling: TemperatureScaling = temperature_scaling

    def __call__(self, vector: AnnealingState[Sequence[float]]) -> Sequence[float]:
        return self._vector_type(
            (2.0*self._random()-1) * self._epsilon * self._temperature_scaling(vector.temperature) + x
            for x in vector.current_solution
        )


class IntegerVectorNeighbourhood:
    """
    Represents a neighbourhood function for integer vectors.

    This class is designed to create a randomized neighbourhood of an input integer vector.
    It generates a new vector by adding a random value (within a specified range defined
    by epsilon) to each element of a given vector. The user can specify the random number
    generator, epsilon value, and the desired return type of the vector.

    Attributes:
        epsilon (int): Defines the magnitude of random changes applied to each element
            in the vector.
        random (RandomNumberGenerator): The random number generator used to produce
            random values for modifying vector elements.
        vector_type (Callable[[Iterable[int]], Sequence[int]]): A callable (such as a
            type) used to define the return type of the generated vector.
    """
    def __init__(
            self,
            epsilon: int = 1,
            random: RandomNumberGenerator = builtin_random,
            vector_type: Callable[[Iterable[int]], Sequence[int]] = tuple,
            temperature_scaling: TemperatureScaling = no_temperature_scaling
    ):
        self._epsilon: int = epsilon
        self._random: RandomNumberGenerator = random
        self._vector_type: Callable[[Iterable[int]], Sequence[int]] = vector_type
        self._temperature_scaling: TemperatureScaling = temperature_scaling

    def __call__(self, vector: AnnealingState[Sequence[int]]) -> Sequence[int]:
        return self._vector_type(
            (round(2.0*self._random()-1*self._epsilon * self._temperature_scaling(vector.temperature)) + x)
            for x in vector.current_solution
        )


class SupportsArrayOps(Protocol):
    shape: tuple[int, ...]
    def __add__(self, other) -> Self: ...


class ArrayNeighbourhood[A: SupportsArrayOps]:
    """
    Represents a neighborhood operation on arrays, where random noise is added to
    each element within a specified range.

    This class uses a pseudorandom number generator to add uniform noise to the
    elements of an input array. The range of the noise is controlled by the
    `epsilon` parameter, and an optional `seed` can be provided to ensure
    reproducibility.

    Attributes:
        epsilon (float): Absolute range value in which the uniform random noise is
            generated and applied to the input array.
    """
    def __init__(
        self,
        epsilon: float = 0.1,
        seed: int = 0,
        temperature_scaling: TemperatureScaling = no_temperature_scaling
    ):
        self._epsilon: float = abs(epsilon)
        from altbacken.optional.numpy.random import default_rng
        self._rng = default_rng(seed)
        self._temperature_scaling = temperature_scaling

    def __call__(self, state: AnnealingState[A]) -> A:
        array: A = state.current_solution
        bounds = self._temperature_scaling(state.temperature) * self._epsilon
        return array + self._rng.uniform(low=-bounds, high=bounds, size=array.shape)


