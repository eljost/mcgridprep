#!/usr/bin/env python3

import argparse
import sys

import matplotlib.pyplot as plt
import numpy as np


def run():
    grid = np.load("grid")
    grid -= grid.min()
    grid *= 27.2114

    angles = np.linspace(180, 30, 31, dtype=int)
    bonds = np.linspace(0.6, 3.5, 30)
    A, B = np.meshgrid(angles, bonds)

    states = grid.shape[-1]
    for state in range(states)[:1]:
        fig, ax = plt.subplots()
        fig.suptitle(f"State {state}")
        state_ens = grid[:,:,state]
        state_ens = np.nan_to_num(state_ens)
        min_en = state_ens.min()
        levels = np.linspace(min_en, min_en+10, 35)
        ax.contour(A, B, state_ens, levels=levels)
        plt.show()


if __name__ == "__main__":
    run()
