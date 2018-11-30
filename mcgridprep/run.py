#!/usr/bin/env python3

import argparse
from functools import partial
import multiprocessing
import os
from pathlib import Path
from pprint import pprint
import re
import shutil
import subprocess
import sys
import tempfile
import time


def parse_args(args):
    parser = argparse.ArgumentParser()

    parser.add_argument("job_inputs")
    parser.add_argument("--cpus", type=int, default=1)

    return parser.parse_args(args)

def check_return_codes(fn):
    with open(fn) as handle:
        text = handle.read()

    rc_re = "/rc=_(\w+)_"
    return_codes = re.findall(rc_re, text)
    fails = [i for i, rc in enumerate(return_codes)
             if rc != "RC_ALL_IS_WELL"
    ]
    if len(return_codes) == 0 or fails:
        print(f"FAIL {fn} ({[return_codes[i] for i in fails]})")


def run_job(job_input, save_path):
    start = time.time()
    with tempfile.TemporaryDirectory() as tmp_dir:
        print(f"Running {job_input} in {tmp_dir}")
        out_path = Path(job_input).with_suffix(".out")
        shutil.copy(job_input, tmp_dir)
        args = f"pymolcas -b0 {job_input} -oe {out_path}".split()

        proc = subprocess.Popen(args, cwd=tmp_dir)
        proc.wait()
        out_saved = save_path / Path(out_path).name
        shutil.copy(tmp_dir / out_path, out_saved)

    end = time.time()
    duration = end - start
    mins = duration / 60
    print(f"... calculations in {job_input} took {mins:.1f} min")
    sys.stdout.flush()
    check_return_codes(out_saved)


def run():
    args = parse_args(sys.argv[1:])

    job_inputs = args.job_inputs
    cpus = args.cpus

    with open(job_inputs) as handle:
        job_inputs = handle.read().strip().split("\n")
    print(f"Loaded {len(job_inputs)} job inputs.")

    cwd = Path(os.getcwd())
    save_path = cwd / "out"
    try:
        os.mkdir(save_path)
    except FileExistsError:
        print("./out already exists.")

    run_part = partial(run_job, save_path=save_path)
    if cpus == 1:
        print("Running in serial mode.")
        [run_part(inp) for inp in job_inputs]
    else:
        left_inp, right_inp, *col_inps = job_inputs
        print("Running in parallel mode.")

        print("Running equilibrium row with 2 processes.")
        with multiprocessing.Pool(2) as pool:
            pool.map(run_part, (left_inp, right_inp))
        print()

        print(f"Running columns with {cpus} processes.")
        print(f"I found a total of {len(col_inps)} columns.")
        with multiprocessing.Pool(cpus) as pool:
            pool.map(run_part, col_inps)


if __name__ == "__main__":
    run()
