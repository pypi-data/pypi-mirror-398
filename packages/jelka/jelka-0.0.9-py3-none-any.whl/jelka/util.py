from typing import Iterable, Tuple, Union

from .types import AABB, Position


def length(position: Union[Position, Tuple[float, float, float]]) -> float:
    """Calculates an absolute value of a point."""
    return Position(*position).magnitude()


def distance(p1: Union[Position, Tuple[float, float, float]], p2: Union[Position, Tuple[float, float, float]]) -> float:
    """Calculates a distance between two points."""
    return (Position(*p1) - Position(*p2)).magnitude()


def bounds(positions: Iterable[Union[Position, Tuple[float, float, float]]]) -> AABB:
    """Calculates a bounding box of positions."""
    min_x = min(pos[0] for pos in positions)
    min_y = min(pos[1] for pos in positions)
    min_z = min(pos[2] for pos in positions)
    max_x = max(pos[0] for pos in positions)
    max_y = max(pos[1] for pos in positions)
    max_z = max(pos[2] for pos in positions)

    return AABB(min_x, min_y, min_z, max_x, max_y, max_z)
