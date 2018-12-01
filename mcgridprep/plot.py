#!/usr/bin/env python3

import argparse
import sys

import matplotlib.pyplot as plt
import numpy as np

from mcgridprep.config import config as CONF
from mcgridprep.helpers import coords_from_spec


def run():
    grid = np.load("grid")
    grid -= grid.min()
    grid *= 27.2114

    coord1_spec = CONF["coord1"]
    coord2_spec = CONF["coord2"]
    coords1, _ = coords_from_spec(*coord1_spec)
    coords2, _ = coords_from_spec(*coord2_spec)
    C1, C2 = np.meshgrid(coords1, coords2)

    states = grid.shape[-1]
    for state in range(states)[:1]:
        fig, ax = plt.subplots()
        fig.suptitle(f"State {state}")
        state_ens = grid[:,:,state]
        state_ens = np.nan_to_num(state_ens)
        min_en = state_ens.min()
        levels = np.linspace(min_en, min_en+10, 35)
        ax.contour(C1, C2, state_ens, levels=levels)
        plt.show()


if __name__ == "__main__":
    run()
