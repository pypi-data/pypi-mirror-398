from copy import copy
from dataclasses import asdict
from typing import Any

from pandas import DataFrame

from altbacken.core.annealing import AnnealingState
from altbacken.internal.report.base import Report


class DataFrameReport(Report[Any]):
    """
    Generates and manages a report as a DataFrame.

    This class allows the collection and management of annealing states and their
    representation in a tabular format using a DataFrame. It's useful for tracking
    and analyzing the states during operations such as optimization processes.

    Attributes:
        frame (DataFrame): A DataFrame representation of all collected annealing states.
    """
    def __init__(self) -> None:
        self._buffer: list[AnnealingState[Any]] = []

    def __call__(self, state: AnnealingState[Any]) -> None:
        self._buffer.append(copy(state))

    @property
    def frame(self) -> DataFrame:
        return DataFrame(map(asdict, self._buffer))