import random
from typing import List, Tuple, Union


class Color(Tuple[float, float, float]):
    """Represents an RGB color."""

    def __new__(cls, red: float, green: float, blue: float):
        return super().__new__(cls, (red, green, blue))

    @property
    def red(self) -> float:
        return self[0]

    @property
    def green(self) -> float:
        return self[1]

    @property
    def blue(self) -> float:
        return self[2]

    def __add__(self, other: "Color") -> "Color":  # pyright: ignore[reportIncompatibleMethodOverride]
        return Color(self.red + other.red, self.green + other.green, self.blue + other.blue)

    def __sub__(self, other: "Color") -> "Color":  # pyright: ignore[reportIncompatibleMethodOverride]
        return Color(self.red - other.red, self.green - other.green, self.blue - other.blue)

    def __mul__(self, other: Union["Color", int, float]) -> "Color":  # pyright: ignore[reportIncompatibleMethodOverride]
        if isinstance(other, Color):
            return Color(self.red * other.red, self.green * other.green, self.blue * other.blue)
        elif isinstance(other, (int, float)):
            return Color(self.red * other, self.green * other, self.blue * other)

        raise TypeError("Unsupported operand type(s) for *: 'Color' and '{}'".format(type(other).__name__))

    def __truediv__(self, other: Union["Color", int, float]) -> "Color":  # pyright: ignore[reportIncompatibleMethodOverride]
        if isinstance(other, Color):
            return Color(self.red / other.red, self.green / other.green, self.blue / other.blue)
        elif isinstance(other, (int, float)):
            return Color(self.red / other, self.green / other, self.blue / other)

        raise TypeError("Unsupported operand type(s) for /: 'Color' and '{}'".format(type(other).__name__))

    def __eq__(self, other) -> bool:
        if not isinstance(other, Color):
            return False

        return self.red == other.red and self.green == other.green and self.blue == other.blue

    def __str__(self) -> str:
        return f"Color({self.red}, {self.green}, {self.blue})"

    def __repr__(self) -> str:
        return f"Color({self.red}, {self.green}, {self.blue})"

    def to_tuple(self) -> Tuple[float, float, float]:
        """Returns the color as a tuple of floats."""
        return self.red, self.green, self.blue

    def to_list(self) -> List[float]:
        """Returns the color as a list of floats."""
        return [self.red, self.green, self.blue]

    def to_write(self) -> Tuple[int, int, int]:
        """Returns the color in a format for the data writer."""

        def round_clamp(value):
            return max(0, min(255, round(value)))

        return round_clamp(self.red), round_clamp(self.green), round_clamp(self.blue)

    def vivid(self):
        """Returns a vivid version of the color."""

        minimal = min(self.red, self.green, self.blue)

        # Remove the smallest component to make the color more vibrant
        if self.red == minimal:
            return Color(0, self.green, self.blue)
        elif self.green == minimal:
            return Color(self.red, 0, self.blue)
        elif self.blue == minimal:
            return Color(self.red, self.green, 0)

        return self

    @staticmethod
    def random() -> "Color":
        """Returns a random color."""
        return Color(random.uniform(0, 255), random.uniform(0, 255), random.uniform(0, 255))
