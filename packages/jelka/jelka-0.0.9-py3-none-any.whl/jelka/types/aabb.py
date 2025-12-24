from dataclasses import dataclass

from .position import Position


@dataclass
class AABB:
    """Represents an Axis-Aligned Bounding Box in 3D space."""

    min_x: float
    """Minimal value on the x-axis."""
    min_y: float
    """Minimal value on the y-axis."""
    min_z: float
    """Minimal value on the z-axis."""
    max_x: float
    """Maximal value on the x-axis."""
    max_y: float
    """Maximal value on the y-axis."""
    max_z: float
    """Maximal value on the z-axis."""

    @property
    def center_x(self) -> float:
        """Center position on the x-axis."""
        return (self.min_x + self.max_x) / 2

    @property
    def center_y(self) -> float:
        """Center position on the y-axis."""
        return (self.min_y + self.max_y) / 2

    @property
    def center_z(self) -> float:
        """Center position on the z-axis."""
        return (self.min_z + self.max_z) / 2

    @property
    def volume(self) -> float:
        """The volume of the AABB."""
        return (self.max_x - self.min_x) * (self.max_y - self.min_y) * (self.max_z - self.min_z)

    def intersects(self, other: "AABB") -> bool:
        """Returns whether this AABB intersects with another AABB."""
        return (
            self.min_x <= other.max_x
            and self.max_x >= other.min_x
            and self.min_y <= other.max_y
            and self.max_y >= other.min_y
            and self.min_z <= other.max_z
            and self.max_z >= other.min_z
        )

    def contains(self, position: "Position") -> bool:
        """Returns whether this AABB contains a specific position."""
        return (
            self.min_x <= position.x <= self.max_x
            and self.min_y <= position.y <= self.max_y
            and self.min_z <= position.z <= self.max_z
        )
