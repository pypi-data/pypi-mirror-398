import os
import sys
import time
from typing import Callable, Dict, List, Union

import jelka_validator.datawriter as dw

from .shapes import Shape
from .types import AABB
from .types import Color
from .types import Position
from .util import bounds


class Jelka:
    """Main class for controlling the tree."""

    def __init__(
        self,
        frame_rate: int = 60,
        initial_color: Color = Color(0, 0, 0),
        number_of_lights: Union[int, None] = None,
        custom_positions: Union[str, None] = None,
        frame_time_warning: bool = True,
    ):
        self.frame_rate: int = frame_rate
        """Frame rate of the pattern."""

        self.frame: int = 0
        """Current frame number."""

        self.start_time: float = time.perf_counter()
        """Time when the pattern was started."""

        self.elapsed_time: float = 0.0
        """Time since the pattern was started."""

        self.positions_raw: Dict[int, Position] = dict()
        """Raw positions of the lights."""

        self.positions_normalized: Dict[int, Position] = dict()
        """Normalized positions of the lights."""

        self.bounds_raw: AABB = AABB(0, 0, 0, 0, 0, 0)
        """Bounds of the tree in raw coordinates."""

        self.bounds_normalized: AABB = AABB(0, 0, 0, 0, 0, 0)
        """Bounds of the tree in normalized coordinates."""

        self.center_raw: Position = Position(0, 0, 0)
        """Center of the tree in raw coordinates."""

        self.center_normalized: Position = Position(0, 0, 0)
        """Center of the tree in normalized coordinates."""

        if custom_positions:
            # Use a custom positions file if provided
            filenames = [custom_positions]

        elif environment_positions := os.getenv("JELKA_POSITIONS"):
            # Use positions file from environment variable if provided
            filenames = [environment_positions]

        else:
            # Provide default file locations
            filenames = [
                os.path.join(os.getcwd(), "positions.csv"),
                os.path.join(os.path.dirname(sys.argv[0]), "positions.csv"),
                os.path.join(os.getcwd(), "../../data/positions.csv"),
                os.path.join(os.path.dirname(sys.argv[0]), "../../data/positions.csv"),
            ]

        # Resolve relative paths to absolute paths
        filenames = [os.path.abspath(filename) for filename in filenames]

        # Try to load positions from various files
        self.load_positions(filenames)

        # Normalize the positions
        self.normalize_positions(0, 1)

        # Get max index of the lights
        if number_of_lights is None:
            number_of_lights = max(self.positions_raw.keys()) + 1

        self.number_of_lights: int = number_of_lights
        """Number of lights the pattern supports."""

        self.lights: List[Color] = [initial_color for _ in range(number_of_lights)]
        """List of colors of the lights."""

        self.objects: List[Shape] = []
        """List of objects in the scene."""

        self.dw = dw.DataWriter(number_of_lights)
        """Direct access to the data writer."""

        self.clear = False
        """Whether to clear the lights before each frame."""

        self.frame_time_warning = frame_time_warning
        """Whether to show warning if frame time exceeds the limit."""

    def load_positions(self, filenames: List[str]):
        """Loads positions from the first available file."""

        for filename in filenames:
            if not os.path.isfile(filename):
                continue

            with open(filename) as file:
                print(f"[LIBRARY] Loading positions from '{filename}'.", file=sys.stderr, flush=True)

                # Read the positions from the file
                for line in file.readlines():
                    line = line.strip()
                    if line == "":
                        continue
                    i, x, y, z = line.split(",")
                    self.positions_raw[int(i)] = Position(float(x), float(y), float(z))

                # Calculate the bounds of the tree
                self.bounds_raw = bounds(self.positions_raw.values())

                # Calculate the center of the tree
                self.center_raw = Position(0, 0, (self.bounds_raw.min_z + self.bounds_raw.max_z) / 2)

                return

        raise FileNotFoundError(f"[LIBRARY] No valid file found to load positions from (attempted: {filenames}).")

    def normalize_positions(
        self,
        l: int = 0,
        r: int = 1,
        mn: Union[int, float, None] = None,
        mx: Union[int, float, None] = None,
    ):
        """Normalizes the positions to the range [l, r]."""

        if mn is None:
            mn = min([pos.x for pos in self.positions_raw.values()])
            mn = min(min([pos.y for pos in self.positions_raw.values()]), mn)
            mn = min(min([pos.z for pos in self.positions_raw.values()]), mn)

        if mx is None:
            mx = max([pos.x for pos in self.positions_raw.values()])
            mx = max(max([pos.y for pos in self.positions_raw.values()]), mx)
            mx = max(max([pos.z for pos in self.positions_raw.values()]), mx)
            mx += 0.01  # to avoid division by zero

        for i, pos in self.positions_raw.items():
            x = (pos.x - mn) / (mx - mn) * (r - l) + l
            y = (pos.y - mn) / (mx - mn) * (r - l) + l
            z = (pos.z - mn) / (mx - mn) * (r - l) + l
            self.positions_normalized[i] = Position(x, y, z)

        # Calculate the bounds of the tree
        self.bounds_normalized = bounds(self.positions_normalized.values())

        # Calculate the center of the tree
        self.center_normalized = Position(
            (self.center_raw.x - mn) / (mx - mn) * (r - l) + l,
            (self.center_raw.y - mn) / (mx - mn) * (r - l) + l,
            (self.center_raw.z - mn) / (mx - mn) * (r - l) + l,
        )

    def set_light(self, i: int, color: Color):
        """Sets the color of the specified light."""
        self.lights[i] = color

    def run(self, callback: Union[Callable[["Jelka"], None], None] = None, init: Union[Callable[["Jelka"], None], None] = None):
        """Runs the main loop of the tree."""

        # Call the init function
        if init is not None:
            print("[LIBRARY] Running the init function.", file=sys.stderr, flush=True)
            init(self)

        print("[LIBRARY] Starting the main loop.", file=sys.stderr, flush=True)

        self.start_time = time.perf_counter()

        while True:
            self.elapsed_time = time.perf_counter() - self.start_time
            current_time = time.perf_counter_ns()

            # Clear the lights if needed
            if self.clear:
                for light in range(self.number_of_lights):
                    self.set_light(light, Color(0, 0, 0))

            # Update the positions of the objects
            for obj in self.objects:
                obj.update_position(self.elapsed_time)

                for light, position in self.positions_normalized.items():
                    if obj.is_inside(position):
                        self.set_light(light, Color(obj.color.red, obj.color.green, obj.color.blue))

            # Call the callback function
            if callback is not None:
                callback(self)

            # Write the frame to the tree
            writable = [light.to_write() for light in self.lights]
            self.dw.write_frame(writable)

            new_time = time.perf_counter_ns()
            frame_time = new_time - current_time
            target_time = 10**9 / self.frame_rate

            if frame_time <= target_time:
                time.sleep((target_time - frame_time) / 10**9)
            elif self.frame_time_warning:
                print(
                    f"[LIBRARY] Warning: Cannot keep up with the frame rate during the frame {self.frame}.",
                    file=sys.stderr,
                    flush=True,
                )
                print(
                    f"[LIBRARY] Frame time: {frame_time} ns, Max frame time: {target_time} ns",
                    file=sys.stderr,
                    flush=True,
                )

            self.frame += 1
