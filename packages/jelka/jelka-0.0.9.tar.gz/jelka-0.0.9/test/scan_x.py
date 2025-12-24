from jelka import Jelka
from jelka.types import Color

axis = 0
threshold = 0.05
dimmer = 0.2

color: Color


def wave(x: float, low: float = -0.2, high: float = 1.2) -> float:
    return 2 * (high - low) * abs(x - round(x)) + low


def init(jelka: Jelka):
    mx = max([pos[axis] for pos in jelka.positions_raw.values()])
    mn = min([pos[axis] for pos in jelka.positions_raw.values()])
    jelka.normalize_positions(0, 1, mn, mx)


def callback(jelka: Jelka):
    global color

    if jelka.frame % 300 == 0:
        color = Color.random().vivid()

    coord = wave(jelka.frame / jelka.frame_rate / 4)

    for light, position in jelka.positions_normalized.items():
        jelka.set_light(light, color if abs(position[axis] - coord) < threshold else color * dimmer)


def main():
    jelka = Jelka(60)
    jelka.run(callback, init)


main()
