from collections.abc import Sequence, Callable, Iterable
from random import randint as builtin_random

from more_itertools import last

from altbacken.core.annealing import RandomNumberRange
from altbacken.core.neighbourhood import Neighbourhood
from altbacken.core.state import AnnealingState


class PermutationNeighbourhood[T](Neighbourhood[Sequence[T]]):
    def __init__(
            self,
            swap_weight: float = 0.7,
            reverse_weight: float = 0.2,
            insert_weight: float = 0.1,
            *,
            seq: Callable[[Iterable[T]], Sequence[T]] = tuple,
            random: RandomNumberRange = builtin_random,
    ):
        if swap_weight < 0:
            raise ValueError("Swap weight must be non-negative")
        if reverse_weight < 0:
            raise ValueError("Reverse weight must be non-negative")
        if insert_weight < 0:
            raise ValueError("Insert weight must be non-negative")
        weight_sum: float = swap_weight + reverse_weight + insert_weight
        if weight_sum <= 0:
            raise ValueError("Weights must sum to positive value")

        self._weights: dict[Callable[[Sequence[T]], Sequence[T]], float] = {
            method: probability / weight_sum
            for method, probability in
            zip((self._swap, self._reverse, self._insert), (swap_weight, reverse_weight, insert_weight))
        }
        self._seq: Callable[[Iterable[T]], Sequence[T]] = seq
        self._random: RandomNumberRange = random

    def __call__(self, state: AnnealingState[Sequence[T]]) -> Sequence[T]:
        value: Sequence[T] = state.current_solution
        p: float = self._random(0, 100) * 0.01
        acc: float = 0.0
        for method, weight in self._weights.items():
            acc += weight
            if p <= acc:
                return self._seq(method(value))
        return self._seq(last(self._weights.keys())(value))

    def _swap(self, value: Sequence[T]) -> Sequence[T]:
        if len(value) <= 1:
            raise ValueError("Cannot swap a sequence of length 1 or less")
        first: int = self._random(0, len(value)-1)
        second: int = (first + self._random(1, len(value)-1)) % len(value)
        return self._seq(
            x if i != first and i != second else value[second] if i == first else value[first]
            for i, x in enumerate(value)
        )

    def _reverse(self, value: Sequence[T]) -> Sequence[T]:
        """
        Reverse a subsequence of a given sequence while maintaining the overall sequence order.

        The function takes a sequence as input, selects a random subsequence using a
        randomly generated start and end index, reverses that subsequence, and returns
        the updated sequence.

        Args:
            value (Sequence[T]): The input sequence to process. Must contain more
                than one element.

        Raises:
            ValueError: If the input sequence length is 1 or less.

        Returns:
            Sequence[T]: A new sequence with the specified subsequence reversed.
        """
        if len(value) <= 1:
            raise ValueError("Cannot reverse a sequence of length 1 or less")
        start: int = self._random(0, len(value)-1)
        end: int = (start + self._random(1, len(value)-1)) % len(value)
        start, end = min(start, end), max(start, end)
        buffer = list(value)
        buffer[start:end + 1] = reversed(buffer[start:end + 1])
        return self._seq(buffer)

    def _insert(self, value: Sequence[T]) -> Sequence[T]:
        if len(value) <= 1:
            raise ValueError("Cannot rotate a sequence of length 1 or less")
        selected: int = self._random(0, len(value)-1)
        position: int = (selected + self._random(1, len(value)-1)) % len(value)
        buffer: list[T] = list(value)
        element: T = buffer.pop(selected)
        if position > selected:
            position -= 1
        buffer.insert(position, element)
        return self._seq(buffer)
