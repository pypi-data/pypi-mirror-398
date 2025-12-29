from collections.abc import Sequence
from json import dump
from pathlib import Path
from typing import TextIO

from altbacken.core.annealing import AnnealingState
from altbacken.internal.analysis.base import Analyzer
from altbacken.internal.report.base import BufferingReport


class JSONLineReport[T](BufferingReport[T]):
    def __init__(self, path: Path, analyzers: Sequence[Analyzer[T]]):
        super().__init__(analyzers)
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._handle: TextIO = self._path.open("w")


    def __call__(self, state: AnnealingState[T]) -> None:
        for analyzer in self._analyzers:
            if result := analyzer(state):
                dump(result, self._handle)
                self._handle.write("\n")


    def close(self):
        self._handle.close()
