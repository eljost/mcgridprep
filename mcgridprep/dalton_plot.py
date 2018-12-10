#!/usr/bin/env python3

import multiprocessing
from pathlib import Path
import re

import matplotlib.pyplot as plt
from natsort import natsorted
import numpy as np

from mcgridprep.helpers import get_meshgrid, get_all_ids, load_coords


def get_energy(fn):
    with open(fn) as handle:
        text = handle.read()
    float_re = "([\d\-\.]+)"
    en_re = f"Final MCSCF energy:\s*{float_re}"
    mobj = re.search(en_re, text)
    return float(mobj[1])


def run():
    cwd = Path(".")
    logs = natsorted(cwd.glob("./*/dalton_xyz.out"))

    # import pdb; pdb.set_trace()
    # id_re = f"{float_re}_{float_re}"
    # ids = [re.match(id_re, str(log)) for log in logs]
    # coord1, coord2 = zip(*ids)
    # print(ids)
    coord1, num1, coord2, num2 = load_coords()
    C1, C2 = get_meshgrid()
    ids = get_all_ids()
    fns = [Path(id_) / "dalton_xyz.out" for id_ in ids]
    with multiprocessing.Pool(4) as pool:
        energies = pool.map(get_energy, fns)
    energies = np.array(energies).reshape(num2, num1)
    # print(energies)
    # print(ids)
    fig, ax = plt.subplots()
    ax.contourf(C1, C2, energies)
    plt.show()




if __name__ == "__main__":
    run()
