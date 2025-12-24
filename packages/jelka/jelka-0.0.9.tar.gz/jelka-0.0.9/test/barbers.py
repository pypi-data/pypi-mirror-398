import math

from jelka import Jelka
from jelka.shapes import Sphere
from jelka.types import Color


def callback(jelka: Jelka):
    cols = [Color(255, 0, 0), Color(0, 0, 255), Color(255, 255, 255)]
    height = [1 - 0.005 * (jelka.frame % 210), 1 - 0.005 * ((jelka.frame + 70) % 210), 1 - 0.005 * ((jelka.frame + 140) % 210)]

    rad = [(1 - height[0]) / 2, (1 - height[1]) / 2, (1 - height[2]) / 2]

    x = [
        0.5 + rad[0] * math.cos(height[0] * 20),
        0.5 + rad[1] * math.cos(height[1] * 20),
        0.5 + rad[2] * math.cos(height[2] * 20),
    ]
    y = [
        0.5 + rad[0] * math.sin(height[0] * 20),
        0.5 + rad[1] * math.sin(height[1] * 20),
        0.5 + rad[2] * math.sin(height[2] * 20),
    ]

    sph = [
        Sphere((x[0], y[0], height[0]), 0.2),
        Sphere((x[1], y[1], height[1]), 0.2),
        Sphere((x[2], y[2], height[2]), 0.2),
    ]

    for light, position in jelka.positions_normalized.items():
        for j in range(0, 3):
            if sph[j].is_inside(position):
                jelka.set_light(light, cols[j])


def main():
    jelka = Jelka(60)
    jelka.run(callback)


main()
