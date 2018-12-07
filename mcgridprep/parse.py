#!/usr/bin/env python3

import argparse
import itertools as it
import logging
from pathlib import Path
from pprint import pprint
import re
import sys

import h5py
import numpy as np

from mcgridprep.config import config as CONF
from mcgridprep.helpers import ind_for_spec, id_for_fn, coords_from_spec, \
                               get_all_ids
import mcgridprep.helpers as helpers


def parse_args(args):
    parser = argparse.ArgumentParser()

    parser.add_argument("--backup", default="./backup")
    parser.add_argument("--out", default="./out")

    return parser.parse_args(args)


def get_ind_funcs():
    coord1_spec = CONF["coord1"]
    coord2_spec = CONF["coord2"]
    coords1, num1 = coords_from_spec(*coord1_spec)
    coords2, num2 = coords_from_spec(*coord2_spec)

    coord1_ind = lambda c1: ind_for_spec(*coord1_spec, c1)
    coord2_ind = lambda c2: ind_for_spec(*coord2_spec, c2)
    return coord1_ind, coord2_ind


def parse_loprop(text):
    pol_re = "Molecular Polarizability\s*" \
             "Tensor\s*" \
             "mat. size =     3x    3\s*" \
             "(.+?)" \
             "\*\*\*\*"
    mobj = re.search(pol_re, text, re.DOTALL)
    pols = np.array(mobj[1].strip().split(), dtype=float)
    return pols


def parse_caspt2(text, skip=None):
    pt2_re =  "CASPT2 Root\s+\d+\s+Total energy:\s+([\d\-\.]+)"
    pt2_energies = [float(e) for e in re.findall(pt2_re, text)]
    return pt2_energies[:-skip]


def parse_logs(fns, grid_dims):
    num2, num1 = grid_dims

    calc_texts = list()
    for fn in fns:
        with open(fn) as handle:
            text = handle.read()
        calc_texts.extend(text.split("Start Module: gateway")[1:])

    logs_expected = num1*num2
    logs_present = len(calc_texts)
    if logs_present != logs_expected:
        logging.warning(f"I was expecting {logs_expected} finished "
                        f"calculations, but found only {logs_present}."
        )

    ids = [helpers.id_from_log(text) for text in calc_texts]
    coord1_ind, coord2_ind = get_ind_funcs()
    inds = [(coord2_ind(c2), coord1_ind(c1)) for c1, c2 in ids]

    if "loprop" in CONF["methods"]:
        print("Found loprop keyword. Parsing polarizabilities.")
        pol_grid_fn = "polarization_grid.npy"
        pol_grid = np.zeros((num2, num1, 6))
        for (c2_ind, c1_ind), text in zip(inds, calc_texts):
            pols = parse_loprop(text)
            pol_grid[c2_ind, c1_ind] = pols
        np.save(pol_grid_fn, pol_grid)
        print(f"Wrote polarizations to '{pol_grid_fn}'")

    states = CONF["ciroot"] if CONF["ciroot"] else 1
    if "caspt2" in CONF["methods"]:
        print("Found caspt2 keyword.")
        pt2_grid_fn = "caspt2_grid.npy"
        pt2_grid = np.zeros((num2, num1, states))
        skip = 6 if "loprop" in CONF["methods"] else None
        for (c2_ind, c1_ind), text in zip(inds, calc_texts):
            pt2_energy = parse_caspt2(text, skip)
            pt2_grid[c2_ind, c1_ind] = pt2_energy
        np.save(pt2_grid_fn, pt2_grid)
        print(f"Wrote CASPT2 energies to '{pt2_grid_fn}'")


def energies_from_h5s(h5_fns, grid_dims, grid_fn, h5_key="SFS_ENERGIES"):
    if len(h5_fns) == 0:
        return
    ids = [id_for_fn(fn.name) for fn in h5_fns]

    coord1_ind, coord2_ind = get_ind_funcs()

    h5 = h5py.File(h5_fns[0], "r")
    ens = h5[h5_key][:]
    states = ens.size

    num2, num1 = grid_dims
    grid = np.zeros((num2, num1, states))
    for id_, h5_fn in zip(ids, h5_fns):
        c1, c2 = id_
        c1_ind = coord1_ind(c1)
        c2_ind = coord2_ind(c2)
        f = h5py.File(h5_fn)
        grid[c2_ind,c1_ind] = f[h5_key][:]

    np.save(grid_fn, grid)
    print(f"Wrote '{grid_fn}'")


def run():
    args = parse_args(sys.argv[1:])

    backup_path = Path(args.backup)
    out_path = Path(args.out)

    coord1_spec = CONF["coord1"]
    coord2_spec = CONF["coord2"]
    coords1, num1 = coords_from_spec(*coord1_spec)
    coords2, num2 = coords_from_spec(*coord2_spec)
    grid_dims = (num2, num1)

    fns = list(out_path.glob("*.out"))
    print("Parsing data from logfiles.")
    parse_logs(fns, grid_dims=grid_dims)
    print()

    meshgrid_fn = "meshgrid.npy"
    np.save("meshgrid", np.meshgrid(coords1, coords2))
    print(f"Wrote coordinate grid to '{meshgrid_fn}'.")
    print()

    print("Parsing data from HDF5 files.")
    cas_h5s = list(backup_path.glob("*.rasscf.h5"))
    print(f"Found {len(cas_h5s)} rasscf HDF5 files.")
    cas_rassi_h5s = list(backup_path.glob("*.rassi_cas.h5"))
    print(f"Found {len(cas_rassi_h5s)} rasscf/rassi HDF5 files.")
    pt2_rassi_h5s = list(backup_path.glob("*.rassi_pt2.h5"))
    print(f"Found {len(pt2_rassi_h5s)} caspt2/rassi HDF5 files.")

    energies_from_h5s(cas_h5s, grid_dims, "rasscf_grid.npy", h5_key="ROOT_ENERGIES")
    energies_from_h5s(cas_rassi_h5s, grid_dims, "rasscf_grid.npy")
    energies_from_h5s(pt2_rassi_h5s, grid_dims, "caspt2_grid.npy")


if __name__ == "__main__":
    run()
