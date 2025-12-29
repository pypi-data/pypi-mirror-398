from collections.abc import Callable
from typing import Self
from operator import and_, or_

from altbacken.core.annealing import StopCondition, AnnealingState


class _CompoundElement[T]:
    def __init__(self, binary_func: Callable[[bool, bool], bool], left: StopCondition[T], right: StopCondition[T]):
        self._binary_func: Callable[[bool, bool], bool] = binary_func
        self._left: StopCondition[T] = left
        self._right: StopCondition[T] = right

    def __call__(self, state: AnnealingState[T]) -> bool:
        return self._binary_func(self._left(state), self._right(state))

    def __str__(self) -> str:
        return f'{self._left} {self._binary_func.__name__.strip("_")} {self._right}'


class CompoundStopCondition[T]:
    def __init__(self, condition: StopCondition[T]):
        self._condition: StopCondition = condition

    def __call__(self, state: AnnealingState) -> bool:
        return self._condition(state)

    def __and__(self, other: StopCondition[T]) -> "CompoundStopCondition[T]":
        return CompoundStopCondition(_CompoundElement(and_, self._condition, other))

    def __or__(self, other: StopCondition[T]) -> "CompoundStopCondition[T]":
        return CompoundStopCondition(_CompoundElement(or_, self._condition, other))

    def __str__(self) -> str:
        return str(self._condition)
