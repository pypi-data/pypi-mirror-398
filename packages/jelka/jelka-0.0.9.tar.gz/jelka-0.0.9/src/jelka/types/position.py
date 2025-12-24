from typing import Tuple


class Position(Tuple[float, float, float]):
    """Represents a position in 3D space."""

    def __new__(cls, x: float, y: float, z: float):
        return super().__new__(cls, (x, y, z))

    @property
    def x(self) -> float:
        return self[0]

    @property
    def y(self) -> float:
        return self[1]

    @property
    def z(self) -> float:
        return self[2]

    def __add__(self, other: "Position") -> "Position":  # pyright: ignore[reportIncompatibleMethodOverride]
        return Position(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: "Position") -> "Position":  # pyright: ignore[reportIncompatibleMethodOverride]
        return Position(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> "Position":  # pyright: ignore[reportIncompatibleMethodOverride]
        return Position(self.x * scalar, self.y * scalar, self.z * scalar)

    def __truediv__(self, scalar: float) -> "Position":  # pyright: ignore[reportIncompatibleMethodOverride]
        return Position(self.x / scalar, self.y / scalar, self.z / scalar)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Position):
            return False

        return self.x == other.x and self.y == other.y and self.z == other.z

    def __str__(self):
        return f"Position({self.x}, {self.y}, {self.z})"

    def __repr__(self):
        return f"Position({self.x}, {self.y}, {self.z})"

    def dot(self, other: "Position") -> float:
        """Calculates the dot product of two positions."""
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other: "Position") -> "Position":
        """Calculates the cross product of two positions."""
        return Position(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )

    def magnitude(self) -> float:
        """Calculates the magnitude of the position."""
        return (self.x**2 + self.y**2 + self.z**2) ** 0.5

    def normalize(self) -> "Position":
        """Returns the normalized position."""
        mag = self.magnitude()
        return self / mag if mag != 0 else self
