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

    coord1, num1, coord2, num2 = load_coords()
    C1, C2 = get_meshgrid(indexing="ij")
    ids = get_all_ids()
    fns = [Path(id_) / "dalton_xyz.out" for id_ in ids]
    with multiprocessing.Pool(4) as pool:
        energies = pool.map(get_energy, fns)
    energies = np.array(energies).reshape(num1, num2)
    energies -= energies.min()
    energies *= 27.2114
    fig, ax = plt.subplots()
    levels = np.linspace(0, 25, 35)
    cf = ax.contourf(C1, C2, energies, levels=levels)
    ax.contour(C1, C2, energies, colors="w", levels=levels)
    fig.colorbar(cf)
    plt.show()


if __name__ == "__main__":
    run()
