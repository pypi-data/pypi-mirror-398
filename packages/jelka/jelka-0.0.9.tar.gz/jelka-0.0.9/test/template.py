from jelka import Jelka


def init(jelka: Jelka):
    pass


def callback(jelka: Jelka):
    pass


def main():
    jelka = Jelka(60)
    jelka.run(callback, init)


main()
