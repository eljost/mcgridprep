#!/usr/bin/env python3

import argparse
from collections import Counter
import itertools as it
import multiprocessing
from pathlib import Path
from pprint import pprint
import os
import shutil
import subprocess
import sys
import time

import numpy as np

from mcgridprep.config import config as CONF
from mcgridprep.elements import ELEMENTS
from mcgridprep.main import setup_2d_scan, make_xyzs
from mcgridprep.templates import ENV

MOL_TPL = ENV.get_template("dalton.mol.tpl")

MOL_FN = "xyz.mol"
DAL_FN = "dalton.dal"


def parse_args(args):
    parser = argparse.ArgumentParser()

    parser.add_argument("--run", action="store_true")
    parser.add_argument("--cpus", type=int, default=4)
    parser.add_argument("--mem", type=int, default=2000)

    return parser.parse_args(args)


def prepare_mol(atoms, coords, basis, charge):
    atom_counter = Counter(atoms)
    elements = list(atom_counter.keys())
    atom_types = len(elements)
    key_func = lambda ac: ac[0]
    atoms_coords_sort = sorted(zip(atoms, coords), key=key_func)
    coords_by_elem = it.groupby(atoms_coords_sort, key=key_func)
    atoms_data = list()
    for elem, elem_coords in coords_by_elem:
        atom_num = atom_counter[elem]
        elem_charge = ELEMENTS[elem].number
        elem_coords = list(elem_coords)
        atoms_data.append((
                    elem_charge,
                    atom_num,
                    elem_coords,
        ))
    sym_str = "" if CONF["dal_sym"] else "NoSymmetry"
    mol = MOL_TPL.render(
                      basis=basis,
                      charge=charge,
                      atoms_data=atoms_data,
                      sym_str=sym_str,
    )
    return mol


def make_coords(angle, bond):
    beta = angle/2
    alpha = 90 - beta

    sina = np.sin(np.deg2rad(alpha))
    sinb = np.sin(np.deg2rad(beta))
    a = sina * bond
    b = sinb * bond

    coords = np.array((
                (0, 0, 0),
                (0, b, a),
                (0, -b, a),
    ))
    return coords


def make_jobs(coords1, coords2, atoms, basis, charge, id_fmt, prev_id=None):
    jobs = list()
    prev_jobs = list()
    coords_grid = list(it.product(coords1, coords2))
    ids = [id_fmt.format(c1, c2) for c1, c2 in coords_grid]
    coords = [make_coords(c1, c2) for c1, c2 in coords_grid]
    mols = [prepare_mol(atoms, c, basis, charge) for c in coords]
    for i, id_ in enumerate(ids):
        dir_ = Path(id_)
        try:
            os.mkdir(dir_)
        except FileExistsError:
            pass
        mol_path = dir_ / MOL_FN
        dal_path = dir_ / DAL_FN
        with open(mol_path, "w") as handle:
            handle.write(mols[i])
        shutil.copy(CONF["dal"], dal_path)

        jobs.append(id_)
        prev_jobs.append(prev_id)
        prev_id = id_
    return jobs, prev_jobs


def prepare_job_dirs():
    print("Job configuration")
    pprint(CONF)

    coord1_spec = CONF["coord1"]
    coord2_spec = CONF["coord2"]
    c_eq = CONF["coord_eq"]
    coords = setup_2d_scan(coord1_spec, coord2_spec, c_eq)

    id_fmt = CONF["id_fmt"]
    left_right = [list(it.product(c1, c2)) for c1, c2 in coords[:2]]
    left_right_ids = [id_fmt.format(*cs)
                      for cs in it.chain(left_right[0][::-1], left_right[1])]

    atoms = "O H H".split()
    basis = CONF["basis"]
    charge = CONF["charge"]

    # Expand the up and down coords into two parts of one row
    job_dict = dict()
    for coords_name, (coords1, coords2) in zip(("left", "right"), coords[:2]):
        jobs, prev_jobs = make_jobs(coords1, coords2, atoms, basis, charge, id_fmt)
        job_dict[coords_name] = (jobs, prev_jobs)
        print(jobs)
        print(prev_jobs)

    # Expand up down into their respective columns
    for coords_name, (coords1, coords2) in zip(("down", "up"), coords[2:]):
        for prev_id, col in zip(left_right_ids, coords1):
            # Have to set the appropriate prev_id somehow
            jobs, prev_jobs = make_jobs([col, ], coords2, atoms, basis,
                                        charge, id_fmt, prev_id=prev_id)
            col_name = f"{coords_name}_{col:.2f}"
            job_dict[col_name] = (jobs, prev_jobs)
            print(jobs)
            print(prev_jobs)
            print()
    return job_dict


def run_job(job_dir, prev_job_dir=None):
    start = time.time()
    print(f"Running {job_dir}")
    if prev_job_dir is None:
        # prev_job_dir = "/scratch/wasser_dalton/start"
        cwd = Path(".").resolve()
        prev_job_dir = cwd / "start"

    cur_path = Path(job_dir).resolve()
    prev_path = Path(prev_job_dir).resolve()
    prev_sirius = prev_path / "SIRIUS.RST"
    shutil.copy(prev_sirius, cur_path)
    args = f"dalton -mb {MEM} -put SIRIUS.RST -get SIRIUS.RST {DAL_FN} {MOL_FN}".split()
    proc = subprocess.Popen(args, cwd=cur_path)
    proc.wait()
    end = time.time()
    duration = end - start
    mins = duration / 60
    print(f"... calculations in {job_dir} took {mins:.1f} min")
    cur_sirius = cur_path / f"dalton_xyz.SIRIUS.RST"
    shutil.move(cur_sirius, cur_path / "SIRIUS.RST")


def run_part(args):
    job_dirs, prev_job_dirs = args
    for job_dir, prev_dir in zip(job_dirs, prev_job_dirs):
        run_job(job_dir, prev_dir)


def run():
    args = parse_args(sys.argv[1:])

    cpus = args.cpus
    global MEM
    MEM = args.mem

    job_dict = prepare_job_dirs()
    print(job_dict)
    # left, prev_left  = job_dict["left"]
    # import pdb; pdb.set_trace()
    # run_job(left[0], prev_left[0])
    # run_job(left[1], prev_left[1])

    if args.run:
        start = time.time()
        left_right = (job_dict["left"], job_dict["right"])
        with multiprocessing.Pool(2) as pool:
            pool.map(run_part, left_right)

        cols = [v for k, v in job_dict.items() if k not in ("left", "right")]
        with multiprocessing.Pool(cpus) as pool:
            pool.map(run_part, cols)
        end = time.time()
        duration = end - start
        print(f"Calculations took {duration/60:.1f} min.")


if __name__ == "__main__":
    run()
