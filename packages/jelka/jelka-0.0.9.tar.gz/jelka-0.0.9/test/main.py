from simulation import Simulation

from subprocess import Popen, PIPE
import sys
import time
from jelka_validator.datareader import DataReader


if __name__ == "__main__":
    # Popen(["-m", "writer.py"], executable=sys.executable, stdout=PIPE)
    # Popen(["writer.exe"], stdout=PIPE)
    smreka = {}
    with open("positions.csv") as f:
        for line in f.readlines():
            line = line.strip()
            if line == "":
                continue
            i, x, y, z = line.split(",")
            smreka[int(i)] = (float(x), float(y), float(z))

    with Popen([sys.executable, "rotating_full.py"], stdout=PIPE) as p:
        sim = Simulation(smreka)
        dr = DataReader(p.stdout.read1)  # type: ignore
        dr.update()
        # assert dr.header is not None
        sim.init()
        time.sleep(1)
        while sim.running:
            c = next(dr)
            # assert all(c[i] == c[0] for i in range(len(c)))
            dr.user_print()
            sim.set_colors(dict(zip(range(len(c)), c)))
            sim.frame()
        sim.quit()
