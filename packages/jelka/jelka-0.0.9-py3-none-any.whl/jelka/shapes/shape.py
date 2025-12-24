from abc import ABC, abstractmethod

from ..types import Color, Position


class Shape(ABC):
    """Base class for all shapes."""

    color: Color = Color(0, 0, 0)
    """Color of the shape."""

    @abstractmethod
    def is_inside(self, position: Position) -> bool:
        """Returns whether the given position is inside the shape."""
        raise NotImplementedError

    @abstractmethod
    def update_position(self, time: float):
        """Updates the position of the shape."""
        raise NotImplementedError
