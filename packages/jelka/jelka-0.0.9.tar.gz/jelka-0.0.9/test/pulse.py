import math

from jelka import Jelka
from jelka.types import Color, Position
from jelka.util import distance

color: Color


def callback(jelka: Jelka):
    global color

    if jelka.frame % 10 == 0:
        color = Color.vivid(Color.random())

    sphere_center = Position(0.25, 0.25, 0.5)
    rad2 = (math.e ** (math.sin(jelka.frame / jelka.frame_rate * 2))) / 3
    rad1 = (math.e ** (math.cos(jelka.frame / jelka.frame_rate * 2))) / 3

    cnt = 0

    for light, position in jelka.positions_normalized.items():
        dist = distance(sphere_center, position)
        if rad1 >= dist >= rad2:
            cnt += 1
            j = dist / rad1
            if jelka.lights[light] == Color(0, 0, 0):
                jelka.set_light(
                    light,
                    Color(j * color.red, j * color.green, j * color.blue),
                )
            else:
                jelka.set_light(
                    light,
                    Color(j * jelka.lights[light].red, j * jelka.lights[light].green, j * jelka.lights[light].blue),
                )
        else:
            jelka.set_light(light, Color(0, 0, 0))

    if cnt == 0:
        jelka.frame += 2


def main():
    jelka = Jelka(60)
    jelka.run(callback)


main()
