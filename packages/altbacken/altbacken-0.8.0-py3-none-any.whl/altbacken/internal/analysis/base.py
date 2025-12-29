from collections.abc import Callable
from typing import TypedDict, Required, Literal, NotRequired, ReadOnly

from altbacken.core.annealing import AnnealingState

type JSONType = int | float | str | None | bool | list[JSONType] | dict[str, JSONType]


class AnalysisResult(TypedDict, total=False):
    """
    Representation of the analysis result as a structured dictionary.

    This class inherits from TypedDict and provides a structured description
    for an analysis result. It ensures type checking and restricts the usage
    of specific fields while enabling optional fields. This design is used
    primarily for standardizing how analysis outcomes are captured and processed.

    Attributes:
        topic (str): A required field representing the main subject or theme
            of the analysis result.
        level (Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], optional):
            An optional field indicating the severity level of the result.
        message (str, optional): An optional descriptive message that provides
            additional context or information about the result.
    """
    topic: Required[str]
    level: NotRequired[Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]]
    value: NotRequired[ReadOnly[JSONType]]
    message: NotRequired[str]


type Analyzer[T] = Callable[[AnnealingState[T]], AnalysisResult | None]


def noop_analyzer[T](_: AnnealingState[T]) -> AnalysisResult | None:
    """
    Performs a no-operation analysis on the provided annealing state.

    This analyzer function takes an AnnealingState instance and returns a minimal
    analysis result with a static topic "noop". It is intended as a placeholder
    or default behavior when no specific analysis is required or if test data is required.

    Args:
        _: AnnealingState[T]: The state of annealing to be analyzed.

    Returns:
        AnalysisResult | None: A dictionary containing the fixed topic "noop"
        or None.
    """
    return {"topic": "noop"}
