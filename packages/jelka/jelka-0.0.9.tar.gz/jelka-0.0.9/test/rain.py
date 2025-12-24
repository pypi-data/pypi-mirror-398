import random as r

from jelka import Jelka
from jelka.shapes import Sphere
from jelka.types import Color


def init(jelka: Jelka):
    jelka.clear = True

    for i in range(0, 10):
        sphere = Sphere(
            (0.5 + r.uniform(-0.2, 0.2), 0.5 + r.uniform(-0.2, 0.2), 1 + r.uniform(0.0, 1.0)),
            0.1,
            Color(2, 0, 121),
        )

        sphere.path.add_position(
            sphere.center,
            3 + r.uniform(-1.0, 1.0),
        )

        sphere.path.add_position(
            (r.uniform(-1.0, 1.0), r.uniform(-1.0, 1.0), -0.5 + r.uniform(-2.0, 0.4)),
            1 + r.uniform(-0.2, 0.2),
        )

        jelka.objects.append(sphere)


def callback(jelka: Jelka):
    return None


def main():
    jelka = Jelka(60)
    jelka.run(callback, init)


main()
