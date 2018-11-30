#!/usr/bin/env python3

import argparse
import itertools as it
from pathlib import Path
import re
import sys

import h5py
import numpy as np


def parse_args(args):
    parser = argparse.ArgumentParser()

    parser.add_argument("backup_dir")

    return parser.parse_args(args)


def id_from_fn(fn, types):
    regex = "(\d+)_([\d\.]+)\."
    mobj = re.match(regex, str(fn))
    c1, c2 = [t(val) for t, val in zip(types, mobj.groups())]
    return c1, c2

def ind_from_spec(start, end, step, val):
    return int((val-start)/step * np.sign(end-start))


def run():
    args = parse_args(sys.argv[1:])

    backup_dir = args.backup_dir

    cwd = Path(".")
    ras_h5s = list(cwd.glob("*rasscf.h5"))
    ids = [id_from_fn(fn, (int, float)) for fn in ras_h5s]
    print(f"Found {len(ras_h5s)} rasscf HDF5 files.")
    print(ids)

    # Determine number of states from the first H5 file
    h5 = h5py.File(ras_h5s[0])
    ens = h5["ROOT_ENERGIES"][:]
    states = ens.size

    angles = np.linspace(180, 30, 31, dtype=int)
    bonds = np.linspace(0.6, 3.5, 30)
    angle_ind = lambda a: ind_from_spec(180, 30, 5, a)
    # bond_ind = lambda b: ind_from_spec(0.6, 3.5, 0.1, b)
    bond10_ind = lambda b: ind_from_spec(6, 35, 1, b*10)

    grid = np.zeros((bonds.size, angles.size, states))

    for ras_h5 in ras_h5s:
        angle, bond = id_from_fn(ras_h5, (int, float))
        a_ind = angle_ind(angle)
        b_ind = bond10_ind(bond)
        f = h5py.File(ras_h5)
        grid[b_ind, a_ind] = f["ROOT_ENERGIES"][:]

    with open("grid", "wb") as handle:
        np.save(handle, grid)


if __name__ == "__main__":
    run()
