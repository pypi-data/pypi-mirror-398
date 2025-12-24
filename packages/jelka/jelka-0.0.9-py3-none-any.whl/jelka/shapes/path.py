import math
from typing import List, Tuple, Union

from ..types import Position


class Path:
    """A path is a sequence of positions that the shape should move through."""

    def __init__(self):
        self.positions: List[Position] = []
        self.durations: List[float] = []
        self.loop = True

    def add_position(self, position: Union[Position, Tuple[float, float, float]], time: float):
        """Adds a position to the path."""

        self.positions.append(Position(*position))
        self.durations.append(time)

    def current_position(self, time: float) -> Position:
        """Returns the current position on the path at the given time."""

        total = 0
        for i in range(len(self.durations)):
            total += self.durations[i]

        if self.loop:
            time = time - math.floor(time / total) * total

        for i in range(len(self.durations)):
            if time <= self.durations[i]:
                # Linear interpolation between this and next position component-wise
                t = time / self.durations[i]
                if i == len(self.positions) - 1:
                    return self.positions[i]
                return Position(
                    self.positions[i][0] + t * (self.positions[i + 1][0] - self.positions[i][0]),
                    self.positions[i][1] + t * (self.positions[i + 1][1] - self.positions[i][1]),
                    self.positions[i][2] + t * (self.positions[i + 1][2] - self.positions[i][2]),
                )
            time -= self.durations[i]

        return self.positions[-1]
