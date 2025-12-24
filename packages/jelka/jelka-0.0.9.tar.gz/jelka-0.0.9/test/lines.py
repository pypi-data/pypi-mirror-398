from jelka import Jelka
from jelka.types import Color


color: Color = Color.random().vivid()
spawn_rate: int = 40
line_length: int = 10


def callback(jelka: Jelka):
    global color
    global spawn_rate
    global line_length

    if (jelka.frame % spawn_rate) < line_length:
        jelka.set_light(0, color=color)
    else:
        jelka.set_light(0, color=Color(0, 0, 0))
        color = Color.random().vivid()

    for i in reversed(range(1, jelka.number_of_lights)):
        jelka.set_light(i, jelka.lights[i - 1])


def main():
    jelka = Jelka(40)
    jelka.run(callback)


main()
