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

    pol_grid = "polarization_grid.npy"
    if os.path.exists(pol_grid):
        print("Found grid with polarizations.")
        pols = np.load(pol_grid)
        fig, axs = plt.subplots(3, sharex=True, sharey=True)
        axx = pols[:,:,0]
        ayy = pols[:,:,2]
        azz = pols[:,:,5]
        comps = "xx yy zz".split()
        label = "$\\alpha_{xx}$"

        pols_ = np.concatenate((axx.flatten(), ayy.flatten(), azz.flatten()))
        min_ = pols_.min()
        max_ = pols_.max()
        # levels = np.linspace(min_, .5*max_, 75)
        levels = np.linspace(0, min(100, .5*max_), 75)
        # levels = np.logspace(0, 2.25, 125)

        for ax, alpha, comp in zip(axs, (axx, ayy, azz), comps):
            conf = ax.contourf(C1, C2, alpha, levels=levels)
            ax.set_title(f"$\\alpha_{{{comp}}}$")
            ax.set_ylabel(CONF["coord2_lbl"])
        ax.set_xlabel(CONF["coord1_lbl"])
        cbar = fig.colorbar(conf, ax=axs.ravel().tolist())
        cbar.set_label("$\\alpha$ / au")
        fig.savefig("polarizations.pdf")
        plt.show()

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
    # # As we will never reach 0 with logspace ...
    # levels[0] = 0.0
    for state in range(states):
        fig, ax = plt.subplots()
        fig.suptitle(f"{title}, State {state}")
        state_ens = energies[:,:,state]
        state_ens -= state_ens.min()
        state_ens = np.nan_to_num(state_ens)
        min_ind = np.unravel_index(state_ens.argmin(), state_ens.shape)
        x_min = C1[min_ind]
        y_min = C2[min_ind]
        conf = ax.contourf(C1, C2, state_ens, levels=levels)
        x_lims = ax.get_xlim()
        y_lims = ax.get_ylim()
        # ax.contour(C1, C2, state_ens, levels=levels, colors="w", linewidths=1)
        ax.scatter(x_min, y_min, s=10, c="w")
        # ax.vlines(x_min, y_lims[0], y_min, color="white", linestyle="--")
        # ax.hlines(y_min, x_lims[0], x_min, color="white", linestyle="--")
        ax.set_xlabel(CONF["coord1_lbl"])
        ax.set_ylabel(CONF["coord2_lbl"])
        ax.annotate(f"({x_min}°, {y_min:.2f} Å)", (x_min, y_min), color="white",
                    xytext=(x_min+1, y_min+0.05))
        cb = fig.colorbar(conf)
        cb.set_label("$\Delta E / eV$")
        plt.show()
        out_fn = f"{title_slug}_state_{state:02d}.pdf"
        fig.savefig(out_fn)
        print(f"Wrote {out_fn}")


if __name__ == "__main__":
    run()
