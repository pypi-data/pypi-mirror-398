from collections.abc import Sequence
from pathlib import Path
from typing import Literal
from warnings import warn

try:
    from pandas import DataFrame
    from plotnine import ggplot, aes, geom_point, geom_line, ggtitle, ylab
except ImportError:
    raise ImportError("Plotnine is not installed. Please install plotnine to use this feature: altbacken[plotnine].")

from altbacken.internal.analysis.base import Analyzer
from altbacken.internal.report.base import BufferingReport


class ScatterPlotReport(BufferingReport[float | int]):
    """
    A class for generating scatter plot reports.

    The ScatterPlotReport class is a specialized implementation of the BufferingReport
    that focuses on creating scatter plot visualizations from buffered data. This class
    allows users to save plots as image files with specified configurations for resolution,
    size, and unit of measurement. It is optimized to handle sequences of analyzers producing
    data for visualization purposes.

    Attributes:
        analyzers (Sequence[Analyzer[float | int]]): Sequence of analyzers to be used for
            data processing and visualization.
        path (Path): Directory path where the scatter plot images will be saved.
        dpi (int): The resolution of output plot images, measured in dots per inch.
        size (tuple[int, int]): The dimensions of the output plots specified as
            (width, height).
        unit (Literal["in", "cm", "mm"]): Unit of measurement used for the plot size,
            default is millimeters ("mm").
    """
    def __init__(
        self,
        analyzers: Sequence[Analyzer[float | int]],
        path: Path = Path(),
        dpi: int = 300,
        size: tuple[int, int] = (150, 100),
        unit: Literal["in", "cm", "mm"] = "mm"
    ):
        super().__init__(analyzers)
        self._path: Path = path
        self._path.mkdir(parents=True, exist_ok=True)
        self._dpi: int = dpi
        self._size: tuple[int, int] = size
        self._unit: Literal["in", "cm", "mm"] = unit

    def _convert_to_dataframe(self, name: str) -> DataFrame:
        return DataFrame(self._buffers[name])

    def _create_plot(self, name: str) -> None:
        df: DataFrame = self._convert_to_dataframe(name)
        if "value" not in df.columns:
            warn(ResourceWarning(f"Column 'value' not found in dataframe for {name}"))
        else:
            plot = ggplot(df, aes(x="iteration", y="value")) + geom_line() + ggtitle(name) + ylab(name)
            plot.save(
                self._path / f"{name}.png",
                dpi=self._dpi,
                width=self._size[0],
                height=self._size[1],
                limitsize=False,
                units=self._unit
            )

    def close(self) -> None:
        for name in self._buffers:
            self._create_plot(name)


