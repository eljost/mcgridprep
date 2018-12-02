#!/usr/bin/env python3

import argparse
import os
import sys

import matplotlib.pyplot as plt
import numpy as np

from mcgridprep.config import config as CONF
from mcgridprep.helpers import coords_from_spec, slugify


def parse_args(args):
    parser = argparse.ArgumentParser()

    parser.add_argument("--levels", type=int, default=35)

    return parser.parse_args(args)

def run():
    args = parse_args(sys.argv[1:])

    meshgrid_fn = "meshgrid.npy"
    meshgrid = np.load("meshgrid.npy")
    C1, C2 = meshgrid
    print(f"Read coordinates from '{meshgrid_fn}'")

    ras_grid = "rasscf_grid.npy"
    if os.path.exists(ras_grid):
        print("Found grid with &rasscf energies.")
        ras_energies = np.load(ras_grid)
        ras_energies *= 27.2114
        plot_grid(C1, C2, ras_energies, title="CASSCF")

    pt2_grid = "caspt2_grid.npy"
    if os.path.exists(pt2_grid):
        print("Found grid with &caspt2 energies.")
        pt2_energies = np.load(pt2_grid)
        pt2_energies *= 27.2114
        plot_grid(C1, C2, pt2_energies, title="(MS)-CASPT2")


def plot_grid(C1, C2, energies, title="", level_num=35):
    states = energies.shape[-1]
    title_slug = slugify(title)

    levels = np.linspace(0, 5, level_num)**2
    # levels = np.logspace(-4, 2.5, 20, base=2)
    for state in range(states):
        fig, ax = plt.subplots()
        fig.suptitle(f"{title}, State {state}")
        state_ens = energies[:,:,state]
        state_ens -= state_ens.min()
        state_ens = np.nan_to_num(state_ens)
        ax.contour(C1, C2, state_ens, levels=levels)
        ax.set_xlabel(CONF["coord1_lbl"])
        ax.set_ylabel(CONF["coord2_lbl"])
        plt.show()
        out_fn = f"{title_slug}_state_{state:02d}.pdf"
        fig.savefig(out_fn)
        print(f"Wrote {out_fn}")


if __name__ == "__main__":
    run()
