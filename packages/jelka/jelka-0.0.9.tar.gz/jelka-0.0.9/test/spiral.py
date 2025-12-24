import math
from typing import List

from jelka import Jelka
from jelka.shapes import Sphere
from jelka.types import Color, Position

normalized: List[Position]
color: Color


def init(jelka: Jelka):
    global normalized

    normalized = [Position(0, 0, 0)] * jelka.number_of_lights

    min_x = min([pos.x for pos in jelka.positions_raw.values()])
    max_x = max([pos.x for pos in jelka.positions_raw.values()])
    min_y = min([pos.y for pos in jelka.positions_raw.values()])
    max_y = max([pos.y for pos in jelka.positions_raw.values()])
    min_z = min([pos.z for pos in jelka.positions_raw.values()])
    max_z = max([pos.z for pos in jelka.positions_raw.values()])

    for light, position in jelka.positions_raw.items():
        normalized[light] = Position(
            (position.x - min_x) / (max_x - min_x + 0.01),
            (position.y - min_y) / (max_y - min_y + 0.01),
            (position.z - min_z) / (max_z - min_z + 0.01),
        )


def callback(jelka: Jelka):
    global color

    height = 1 - 0.0075 * (jelka.frame % 150)

    if height == 1:
        color = Color.vivid(Color.random())

    rad = 1 / 2 - height / 2
    x = 0.5 + rad * math.cos(height * 20)
    y = 0.5 + rad * math.sin(height * 20)

    sphere = Sphere((x, y, height), 0.1)

    for i in range(len(jelka.lights)):
        position = normalized[i]
        if sphere.is_inside(position):
            jelka.set_light(i, color)
        # else:
        #   jelka.set_light(i, Color(0, 0, 0))


def main():
    jelka = Jelka(60)
    jelka.run(callback, init)


main()
