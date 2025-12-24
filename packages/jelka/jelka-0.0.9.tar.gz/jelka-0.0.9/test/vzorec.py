from jelka import Jelka
from jelka.types import Color


def callback(jelka: Jelka):
    jelka.set_light(0, color=Color(0, 255, 0))
    jelka.set_light(1, color=Color(0, 255, 0))
    jelka.set_light(2, color=Color(0, 255, 0))
    jelka.set_light(3, color=Color(0, 255, 0))


def main():
    jelka = Jelka(60)
    jelka.run(callback)


main()
