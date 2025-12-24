from typing import Protocol


class Neighbourhood[T](Protocol):
    """
    Represents a neighbourhood protocol for defining neighbours of a data point.

    Attributes:
        None.
    """
    def __call__(self, reference: T) -> T:
        """
        Gets a neighbour of the given reference.

        Args:
            reference: Data point for which a neighbour is to be found.

        Returns:
            Neighbour of the given reference.
        """