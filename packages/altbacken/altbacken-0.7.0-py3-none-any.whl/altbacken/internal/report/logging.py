from collections.abc import Sequence, Iterable
from pathlib import Path
from sys import stdout
from typing import TextIO

from altbacken.internal.analysis.base import AnalysisResult, Analyzer
from altbacken.internal.report.base import SimpleReport


class LoguruReport[T](SimpleReport):
    """
    Handles logging of analysis results using Loguru for flexible and structured reporting.

    This class, built upon `SimpleReport`, allows for integrating Loguru-based logging
    into analysis reporting. It accepts analysis results and outputs them to a specified
    log sink, such as a file or standard output, with optional serialization. The
    structure and content of log messages are derived from the analysis result data.

    Attributes:
        analyzers (Sequence[Analyzer[T]]): The sequence of analyzers used for analysis
            reporting.
        sink (Path | TextIO): The logging output destination, which can be a file path
            or a text I/O stream. Defaults to stdout.
        serialize (bool): Indicator whether the logs should be serialized as JSON or not.
    """
    def __init__(
            self,
            analyzers: Sequence[Analyzer[T]],
            sink: Path | TextIO = stdout,
            serialize: bool = True
    ):
        super().__init__(analyzers)
        from altbacken.optional.loguru import logger
        self._logger = logger
        self._logger.remove()
        self._logger.add(sink, serialize=serialize)

    @classmethod
    def _message(cls, result: AnalysisResult) -> str:
        """
        Extracts a string message from a given AnalysisResult object.

        This method interprets the provided AnalysisResult and returns a corresponding
        message string. It supports different structures within the input and handles
        them accordingly, such as extracting a message directly, combining topic and
        value into a formatted string, or returning a topic if provided in other forms.

        Args:
            result (AnalysisResult): The analysis result object from which the message
                is to be derived. It may contain varied structures, including attributes
                for message, topic, or value.

        Returns:
            str: The interpreted message string based on the content of the AnalysisResult.
        """
        match result:
            case {"message": str(message)}: return message
            case {"topic": str(topic), "value": value}: return f"{topic}: {value}"
            case other: return other["topic"]

    def _report_analysis(self, results: Iterable[AnalysisResult]) -> None:
        for result in results:
            self._logger.log(result.get("level", "INFO").upper(), self._message(result), **result)
