import math

from jelka import Jelka
from jelka.types import Color


def callback(jelka: Jelka):
    for light, position in jelka.positions_normalized.items():
        jelka.set_light(
            light,
            Color(
                (position[0] * 255 + math.sin(jelka.elapsed_time + 1) * 255 + 256) % 256,
                (position[1] * 255 + math.sin(jelka.elapsed_time + 2) * 255 + 256) % 256,
                (position[2] * 255 + math.sin(jelka.elapsed_time) * 255 + 256) % 256,
            ).vivid(),
        )


def main():
    jelka = Jelka(60)
    jelka.run(callback)


main()
