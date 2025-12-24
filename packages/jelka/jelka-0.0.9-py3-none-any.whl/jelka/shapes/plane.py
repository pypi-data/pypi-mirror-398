from typing import Union, Tuple

from ..types import Position


class Plane:
    def __init__(
        self,
        center: Union[Position, Tuple[float, float, float]],
        normal: Union[Position, Tuple[float, float, float]],
    ):
        self.center = Position(*center)
        self.normal = Position(*normal)
        self.d = self.center.dot(self.normal)
