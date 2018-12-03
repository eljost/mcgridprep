#!/usr/bin/env python3

import argparse
import itertools as it
from pathlib import Path
from pprint import pprint
import re
import sys

import h5py
import numpy as np

from mcgridprep.config import config as CONF
from mcgridprep.helpers import ind_for_spec, id_for_fn, coords_from_spec, get_all_ids


def parse_args(args):
    parser = argparse.ArgumentParser()

    parser.add_argument("backup_dir")

    return parser.parse_args(args)


def grid_from_rassi_h5s(h5_fns, grid_fn, h5_key="SFS_ENERGIES"):
    if len(h5_fns) == 0:
        return
    ids = [id_for_fn(fn.name) for fn in h5_fns]

    # all_ids_set = set(get_all_ids())
    # missing_ids = all_ids_set - set(ids)
    # print("HDF5 files are missing for:")
    # pprint(missing_ids)

    coord1_spec = CONF["coord1"]
    coord2_spec = CONF["coord2"]
    coords1, num1 = coords_from_spec(*coord1_spec)
    coords2, num2 = coords_from_spec(*coord2_spec)

    coord1_ind = lambda c1: ind_for_spec(*coord1_spec, c1)
    coord2_ind = lambda c2: ind_for_spec(*coord2_spec, c2)

    h5 = h5py.File(h5_fns[0], "r")
    ens = h5[h5_key][:]
    states = ens.size

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

    backup_path = Path(args.backup_dir)

    coord1_spec = CONF["coord1"]
    coord2_spec = CONF["coord2"]
    coords1, _ = coords_from_spec(*coord1_spec)
    coords2, _ = coords_from_spec(*coord2_spec)

    meshgrid_fn = "meshgrid.npy"
    np.save("meshgrid", np.meshgrid(coords1, coords2))
    print(f"Wrote coordinate grid to '{meshgrid_fn}'.")

    cas_h5s = list(backup_path.glob("*.rasscf.h5"))
    print(f"Found {len(cas_h5s)} rasscf HDF5 files.")
    cas_rassi_h5s = list(backup_path.glob("*.rassi_cas.h5"))
    print(f"Found {len(cas_rassi_h5s)} rasscf/rassi HDF5 files.")
    pt2_rassi_h5s = list(backup_path.glob("*.rassi_pt2.h5"))
    print(f"Found {len(pt2_rassi_h5s)} caspt2/rassi HDF5 files.")

    grid_from_rassi_h5s(cas_h5s, "rasscf_grid.npy", h5_key="ROOT_ENERGIES")
    grid_from_rassi_h5s(cas_rassi_h5s, "rasscf_grid.npy")
    grid_from_rassi_h5s(pt2_rassi_h5s, "caspt2_grid.npy")


if __name__ == "__main__":
    run()
