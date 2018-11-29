#!/usr/bin/env python3

import argparse
from functools import partial
import multiprocessing
import os
from pathlib import Path
from pprint import pprint
import shutil
import subprocess
import sys
import tempfile
import time


def parse_args(args):
    parser = argparse.ArgumentParser()

    parser.add_argument("job_inputs")
    parser.add_argument("--cpus", type=int, default=4)

    return parser.parse_args(args)


def run_job(job_input, save_path):
    start = time.time()
    with tempfile.TemporaryDirectory() as tmp_dir:
        print(f"Running {job_input} in {tmp_dir}")
        out_path = Path(job_input).with_suffix(".out")
        shutil.copy(job_input, tmp_dir)
        args = f"pymolcas -b0 {job_input} -oe {out_path}".split()

        proc = subprocess.Popen(args, cwd=tmp_dir)
        proc.wait()
        shutil.copy(tmp_dir / out_path, save_path / Path(out_path).name)

    end = time.time()
    duration = end - start
    mins = duration / 60
    print(f"... calculations in {job_input} took {mins:.1f} min")


def run():
    args = parse_args(sys.argv[1:])

    job_inputs = args.job_inputs
    cpus = args.cpus

    with open(job_inputs) as handle:
        job_inputs = handle.read().split("\n")
    print(f"Loaded {len(job_inputs)} job inputs.")
    left_inp, right_inp, *col_inps = job_inputs

    cwd = Path(os.getcwd())

    run_part = partial(run_job, save_path=cwd)

    print("Running equilibrium row.")
    with multiprocessing.Pool(2) as pool:
        pool.map(run_part, (left_inp, right_inp))

    print("Running columns.")
    with multiprocessing.Pool(cpus) as pool:
        pool.map(run_part, col_inps)


if __name__ == "__main__":
    run()
