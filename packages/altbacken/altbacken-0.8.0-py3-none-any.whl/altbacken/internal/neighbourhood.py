from math import e, log


class LogarithmicTemperatureScaling:
    """
    Applies logarithmic temperature scaling to a given temperature.

    This class is used to scale a temperature value using a logarithmic function
    with a specified logarithmic base. The primary purpose is to transform
    temperature values for scenarios where logarithmic scaling is required.

    Attributes:
        base (float): The logarithmic base used for scaling.
    """
    def __init__(self, base: float = e):
        if base <= 1:
            raise ValueError("Base must be greater than 1")
        self._base = base

    def __call__(self, temperature: float) -> float:
        return log(1.0 + temperature, self._base)


class LinearTemperatureScaling:
    """
    Applies linear temperature scaling to input values.

    This class is used to scale temperature values linearly based on a specified slope.
    It is primarily useful for applications requiring temperature normalization or adjustment.

    Attributes:
        slope (float): Positive scaling factor used for linear adjustment of temperature.
    """
    def __init__(self, slope: float = 0.5):
        if slope <= 0:
            raise ValueError("Slope must be positive")
        self._slope: float = slope

    def __call__(self, temperature: float) -> float:
        return temperature * self._slope


class RootTemperatureScaling:
    """
    A class that applies root-based temperature scaling.

    This class is used to scale a given temperature using a root-based computation
    approach. The scaling involves taking the root of the input temperature with
    a positive root value. This can be used in various applications where root scaling
    is necessary.

    Attributes:
        root (float): The positive root value used for scaling calculations.
    """
    def __init__(self, root: float = 2.0):
        if root <= 1:
            raise ValueError("Root must be greater than 1")
        self._root: float = root

    def __call__(self, temperature: float) -> float:
        return temperature ** (1.0 / self._root)