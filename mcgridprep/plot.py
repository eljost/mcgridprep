#!/usr/bin/env python3

import argparse
import os
import sys

import matplotlib.pyplot as plt
import numpy as np

from mcgridprep.config import config as CONF
from mcgridprep.helpers import coords_from_spec


def parse_args(args):
    parser = argparse.ArgumentParser()

    parser.add_argument("--levels", type=int, default=35)

    return parser.parse_args(args)

def run():
    args = parse_args(sys.argv[1:])

    ras_grid = "rasscf_grid"
    if os.path.exists(ras_grid):
        print("Found grid with &rasscf energies.")
        grid = np.load("rasscf_grid")
        plot_grid(grid)
    else:
        print("Couldn't find any grid data.")


def plot_grid(grid, level_num=35):
    grid *= 27.2114

    coord1_spec = CONF["coord1"]
    coord2_spec = CONF["coord2"]
    coords1, _ = coords_from_spec(*coord1_spec)
    coords2, _ = coords_from_spec(*coord2_spec)
    C1, C2 = np.meshgrid(coords1, coords2)

    states = grid.shape[-1]
    for state in range(states):
        fig, ax = plt.subplots()
        fig.suptitle(f"State {state}")
        state_ens = grid[:,:,state]
        state_ens -= state_ens.min()
        state_ens = np.nan_to_num(state_ens)
        levels = np.linspace(0, 5, level_num)**2
        ax.contour(C1, C2, state_ens, levels=levels)
        plt.show()


if __name__ == "__main__":
    run()
