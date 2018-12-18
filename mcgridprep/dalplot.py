#!/usr/bin/env python3

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from mcgridprep.config import config as CONF
from mcgridprep.helpers import get_meshgrid, get_all_ids, load_coords
from mcgridprep.dalparse import (GRID_FN, ENERGIES_FN, PT2_FN, DPMS_FN,
                                 STAT_POLS_FN)


def plot_energies(C1, C2, energies, title=""):
    fig, ax = plt.subplots()
    levels = np.linspace(0, 15, 35)
    cf = ax.contourf(C1, C2, energies, levels=levels)
    # ax.contour(C1, C2, energies, colors="w", levels=levels, alpha=.2)
    fig.colorbar(cf)
    fig.suptitle(f"$\Delta E$ / eV, {title}")
    return fig


def plot_dpms(C1, C2, dpms):
    fig, axs = plt.subplots(3)
    dpm_levels = np.linspace(0, 2, 30)

    # dpm_levels = np.linspace(dpms.min(), dpms.max(), 75)
    for i in range(3):
        ax = axs[i]
        d = dpms[:, :, i]
        cf = ax.contourf(C1, C2, d, levels=dpm_levels)
    # neg_inds = dpms[:,:,2] < 0
    # c1_neg = C1[neg_inds]
    # c2_neg = C2[neg_inds]
    # scatter_sizes = np.abs(dpms[neg_inds][:,2] * 50)
    # axs[2].scatter(c1_neg, c2_neg, s=scatter_sizes)
    fig.colorbar(cf, ax=axs.ravel().tolist())
    fig.suptitle("Perm. DPM / au")
    return fig


def plot_stat_pols(C1, C2, stat_pols):
    fig, axs = plt.subplots(3)
    pol_levels = np.linspace(0, 50, 30)
    for i in range(3):
        ax = axs[i]
        sp = stat_pols[:, :, i]
        cf = ax.contourf(C1, C2, sp, levels=pol_levels)
        # ax.clabel(cf, colors="w", fmt="%.2f")
        # ax.contour(C1, C2, sp, colors="w", levels=pol_levels)
    fig.suptitle("Stat. polarizabilities / au")
    fig.colorbar(cf, ax=axs.ravel().tolist())
    return fig


def smooth2d():
    stat_pols = np.load(STAT_POLS_FN)
    C1, C2 = get_meshgrid(indexing="ij")
    # plot_stat_pols(C1, C2, stat_pols)
    from scipy.interpolate import Rbf
    axx = stat_pols[:, :, 0]
    nans = np.isnan(axx)
    # mean = axx[~nans].mean()
    # axx[nans] = mean
    axx = np.nan_to_num(axx)
    mean = np.mean(axx)
    high_vals = np.abs(axx-mean) > 2*mean
    axx[high_vals] = mean

    # import pdb; pdb.set_trace()
    # axx = np.nan_to_num(stat_pols[:,:,0])#.ravel()
    # rbf = Rbf(C1.ravel(), C2.ravel(), axx, epsilon=2)
    smooth_vals = np.linspace(0, 1, 11)
    epsilons = np.linspace(0.1, 5, 50)
    import itertools as it
    for sv, eps in it.product(smooth_vals, epsilons):
        break
        # rbf = Rbf(C1, C2, axx, smooth=0.5, epsilon=1)
        rbf = Rbf(C1, C2, axx, smooth=sv, epsilon=eps)
        axx_ = rbf(C1, C2)
        smooth = np.stack((axx, axx_, axx_), axis=2)
        fig = plot_stat_pols(C1, C2, smooth)
        fn = f"smooth_{sv:.1f}_eps_{eps:.1f}.png"
        print(fn)
        fig.savefig(fn, dpi=300)


def run():
    C1, C2 = np.load(GRID_FN)
    cas_energies = np.load(ENERGIES_FN)
    dpms = np.load(DPMS_FN)
    stat_pols = np.load(STAT_POLS_FN)
    pt2_energies = None
    pt2_path = Path(PT2_FN)
    if pt2_path.is_file():
        pt2_energies = np.load(pt2_path)

    not_nan = np.invert(np.isnan(cas_energies))
    cas_energies[not_nan] -= cas_energies[not_nan].min()
    cas_energies *= 27.2114

    if pt2_energies is not None:
        not_nan = np.invert(np.isnan(pt2_energies))
        pt2_energies[not_nan] -= pt2_energies[not_nan].min()
        pt2_energies *= 27.2114
        pt2_fig = plot_energies(C1, C2, pt2_energies, "PC-NEVPT2")
        pt2_fig.savfig("nevpt2_ens.pdf")

    en_fig = plot_energies(C1, C2, cas_energies, "CAS")
    dpm_fig = plot_dpms(C1, C2, dpms)
    pol_fig = plot_stat_pols(C1, C2, stat_pols)

    en_fig.savefig("cas_ens.pdf")
    dpm_fig.savefig("dipoles.pdf")
    pol_fig.savefig("pols.pdf")
    plt.show()


if __name__ == "__main__":
    run()
