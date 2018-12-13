#!/usr/bin/env python3

import argparse
from pathlib import Path
import re
import sys

from natsort import natsorted
import numpy as np
import yaml

from mcgridprep.config import config as CONF
from mcgridprep.helpers import get_meshgrid, get_all_ids, load_coords


GRID_FN = "dal_grid.npy"
ENERGIES_FN = "dal_cas_energies.npy"
PT2_FN = "dal_pt2_energies.npy"
DPMS_FN = "dpms.npy"
STAT_POLS_FN = "stat_pols.npy"


def parse_args(args):
    parser = argparse.ArgumentParser()

    parser.add_argument("--nevpt2", action="store_true",
        help="Parse PC-NEVPT2-energy."
    )
    return parser.parse_args(args)


def get_energy(text):
    float_re = "([\d\-\.]+)"
    en_re = f"Final MCSCF energy:\s*{float_re}"
    mobj = re.search(en_re, text)
    return float(mobj[1])


def get_nevpt2_energies(text):
    regex = "PERTURBATION PC-D\s*(.+?)\n"
    mobj = re.search(regex, text)
    line = mobj[1].strip().split()
    assert len(line) == 4, "Expected only one line with four entries."
    energies = np.array(line[1:], dtype=float)
    return energies


def get_dipole_moment(text):
    dpm_re = "Dipole moment components.+?C m \(/\(10\*\*-30\)\s*(.+?)Units"
    mobj = re.search(dpm_re, text, re.DOTALL)
    arr = np.array(mobj[1].strip().split()).reshape(-1, 4)
    # When using symmetry dalton only prints certain components of the DPM
    # So we determine which components are present and update an array
    # that contains only zeros.
    components_present = arr[:,0]
    comp_inds = {"x": 0, "y": 1, "z": 2}
    inds_present = [comp_inds[comp] for comp in components_present]
    dpm = np.zeros(3)
    dpm[inds_present] = arr[:,1].astype(float)
    return dpm


def get_stat_pol(text):
    regex = "Ex\s*Ey\s*Ez(.+)Static polarizabilities"

    stat_pols = list()
    mobj = re.search(regex, text, re.DOTALL)
    pol = mobj[1].strip().split()
    pol = np.array(pol).reshape(-1, 4)[:,1:].astype(float)
    stat_pol = np.diag(pol)
    return stat_pol


def smooth2d():
    stat_pols = np.load(STAT_POLS_FN)
    C1, C2 = get_meshgrid(indexing="ij")
    # plot_stat_pols(C1, C2, stat_pols)
    from scipy.interpolate import Rbf
    axx = stat_pols[:,:,0]
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
    args = parse_args(sys.argv[1:])

    cwd = Path(".")
    logs = natsorted(cwd.glob("./*/dalton_xyz.out"))

    coord1, num1, coord2, num2 = load_coords()
    C1, C2 = get_meshgrid(indexing="ij")
    cas_energies = np.full_like(C1, np.nan)
    pt2_energies = np.full_like(C1, np.nan)
    dpms = np.full((*C1.shape, 3), np.nan)
    stat_pols = np.full((*C1.shape, 3), np.nan)
    id_fmt = CONF["id_fmt"]
    for (i, j), _ in np.ndenumerate(cas_energies):
        c1 = C1[i,j]
        c2 = C2[i,j]
        id_ = id_fmt.format(c1, c2)
        log_path = Path(f"{c1:.2f}_{c2:.2f}/dalton_xyz.out")
        if not log_path.is_file():
            continue
        with open(log_path) as handle:
            text = handle.read()
        try:
            en = get_energy(text)
            cas_energies[i,j] = en
        except:
            print(f"Error while parsing energy from {id_}")
            continue
        if args.nevpt2:
            try:
                pt2_en = get_nevpt2_energies(text)
                # Using PC-NEVPT2 energy
                pt2_energies[i,j] = pt2_en[2]
            except:
                print(f"Error while parsing PC-NEVPT2 energy from {id_}")
        try:
            dpms[i,j] = get_dipole_moment(text)
        except:
            print(f"Error while parsing dipole moments from {id_}")
        try:
            stat_pol = get_stat_pol(text)
            stat_pols[i,j] = stat_pol
        except:
            print(f"Error while parsing static polarizabilities from {id_}")

    np.save(GRID_FN, (C1, C2))
    np.save(ENERGIES_FN, cas_energies)
    np.save(DPMS_FN, dpms)
    np.save(STAT_POLS_FN, stat_pols)

    yaml_dict = {
        "grid": GRID_FN,
        "energies": ENERGIES_FN,
        "dipoles": DPMS_FN,
        "stat_pols": STAT_POLS_FN,
    }

    if args.nevpt2:
        np.save(PT2_FN, pt2_energies)
        yaml_dict["energies"] = PT2_FN

    with open("dash_stark.yaml", "w") as handle:
        yaml.dump(yaml_dict, handle)


if __name__ == "__main__":
    run()
