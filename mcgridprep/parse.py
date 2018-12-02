#!/usr/bin/env python3

import argparse
import itertools as it
from pathlib import Path
import re
import sys

import h5py
import numpy as np

from mcgridprep.config import config as CONF
from mcgridprep.helpers import ind_for_spec, id_for_fn, coords_from_spec


def parse_args(args):
    parser = argparse.ArgumentParser()

    parser.add_argument("backup_dir")

    return parser.parse_args(args)


def run():
    args = parse_args(sys.argv[1:])

    backup_path = Path(args.backup_dir)

    ras_h5s = list(backup_path.glob("*rasscf.h5"))
    ids = [id_for_fn(fn.name, (int, float)) for fn in ras_h5s]
    assert len(ids) > 0, f"Couldn't find any HD5 files in '{backup_path}'"
    print(f"Found {len(ras_h5s)} rasscf HDF5 files.")

    # Determine number of states from the first H5 file
    h5 = h5py.File(ras_h5s[0])
    ens = h5["ROOT_ENERGIES"][:]
    states = ens.size

    coord1_spec = CONF["coord1"]
    coord2_spec = CONF["coord2"]
    coords1, num1 = coords_from_spec(*coord1_spec)
    coords2, num2 = coords_from_spec(*coord2_spec)

    coord1_ind = lambda c1: ind_for_spec(*coord1_spec, c1)
    coord2_ind = lambda c2: ind_for_spec(*coord2_spec, c2)

    grid = np.zeros((num2, num1, states))

    for id_, ras_h5 in zip(ids, ras_h5s):
        c1, c2 = id_
        c1_ind = coord1_ind(c1)
        c2_ind = coord2_ind(c2)
        f = h5py.File(ras_h5)
        grid[c2_ind,c1_ind] = f["ROOT_ENERGIES"][:]

    with open("rasscf_grid", "wb") as handle:
        np.save(handle, grid)


if __name__ == "__main__":
    run()
