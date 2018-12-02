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

    meshgrid_fn = "meshgrid.npy"
    meshgrid = np.load("meshgrid.npy")
    C1, C2 = meshgrid
    print(f"Read coordinates from '{meshgrid_fn}'")

    ras_grid = "rasscf_grid"
    if os.path.exists(ras_grid):
        print("Found grid with &rasscf energies.")
        ras_energies = np.load("rasscf_grid")
        plot_grid(C1, C2, ras_energies)
    else:
        print("Couldn't find any grid data.")


def plot_grid(C1, C2, energies, level_num=35):
    energies *= 27.2114

    states = energies.shape[-1]
    for state in range(states):
        fig, ax = plt.subplots()
        fig.suptitle(f"State {state}")
        state_ens = energies[:,:,state]
        state_ens -= state_ens.min()
        state_ens = np.nan_to_num(state_ens)
        levels = np.linspace(0, 5, level_num)**2
        ax.contour(C1, C2, state_ens, levels=levels)
        plt.show()


if __name__ == "__main__":
    run()
