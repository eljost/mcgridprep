#!/usr/bin/env python3

import multiprocessing
from pathlib import Path
import re

import matplotlib.pyplot as plt
from natsort import natsorted
import numpy as np

from mcgridprep.config import config as CONF
from mcgridprep.helpers import get_meshgrid, get_all_ids, load_coords


def get_energy(fn):
    with open(fn) as handle:
        text = handle.read()
    float_re = "([\d\-\.]+)"
    en_re = f"Final MCSCF energy:\s*{float_re}"
    mobj = re.search(en_re, text)
    return float(mobj[1])


def get_stat_pol(fn):
    with open(fn) as handle:
        text = handle.read()

    regex = "Ex\s*Ey\s*Ez(.+)Static polarizabilities"

    stat_pols = list()
    mobj = re.search(regex, text, re.DOTALL)
    pol = mobj[1].strip().split()
    pol = np.array(pol).reshape(-1, 4)[:,1:].astype(float)
    stat_pol = np.diag(pol)
    return stat_pol


def run():
    cwd = Path(".")
    logs = natsorted(cwd.glob("./*/dalton_xyz.out"))

    coord1, num1, coord2, num2 = load_coords()
    C1, C2 = get_meshgrid(indexing="ij")
    energies = np.full_like(C1, np.nan)
    stat_pols = np.full((*C1.shape, 3), np.nan)
    id_fmt = CONF["id_fmt"]
    for (i, j), _ in np.ndenumerate(energies):
        c1 = C1[i,j]
        c2 = C2[i,j]
        id_ = id_fmt.format(c1, c2)
        log_path = Path(f"{c1:.2f}_{c2:.2f}/dalton_xyz.out")
        if not log_path.is_file():
            continue
        try:
            en = get_energy(log_path)
            energies[i,j] = en
        except:
            print(f"Error while parsing energy from {id_}")
        try:
            stat_pol = get_stat_pol(log_path)
            stat_pols[i,j] = stat_pol
        except:
            print(f"Error while parsing static polarizabilities from {id_}")

    not_nan = np.invert(np.isnan(energies))
    energies[not_nan] -= energies[not_nan].min()
    energies *= 27.2114
    fig, ax = plt.subplots()
    levels = np.linspace(0, 25, 35)
    cf = ax.contourf(C1, C2, energies, levels=levels)
    ax.contour(C1, C2, energies, colors="w", levels=levels)
    fig.colorbar(cf)
    plt.show()

    fig, axs = plt.subplots(3)
    pol_levels = np.linspace(0, 50, 30)
    for i in range(3):
        ax = axs[i]
        sp = stat_pols[:,:,i]
        cf = ax.contourf(C1, C2, sp, levels=pol_levels)
        # ax.contour(C1, C2, sp, colors="w", levels=pol_levels)
    fig.colorbar(cf, ax=axs.ravel().tolist())
    plt.show()


if __name__ == "__main__":
    run()
