#!/usr/bin/env python3

import argparse
# from copy import import copy
import itertools as it
from pprint import pprint
import sys
import textwrap

import jinja2
import numpy as np

TPL_STR = """
>> export backup_path={{ backup_path }}
{% if inporb %}
>> copy {{ inporb }} $Project.RasOrb
{% endif %}

{% for id_ in ids %}
&gateway
xbas
  {{ basis }}
 zmat
  {{ zmats[loop.index0] }}
 end of zmat
 ricd

&seward

{% if hf %}
&scf
 {% if spin > 1 %}
 uhf
 {% endif %}
 charge
  {{ charge }}
 spin
  {{ spin }}
{% endif %}

{% if mp2 %}
&mbpt2
{% endif %}

{% if cas %}
&rasscf
 charge
  {{ charge }}
 spin
  {{ spin }}
 fileorb
  $Project.RasOrb
 {% if ciroot %}
  ciroot
   {{ ciroot }} {{ ciroot }} 1
 {% endif %}
*>> copy $Project.RasOrb $backup_path/$Project.{{ id_ }}.RasOrb
>> copy $Project.RasOrb {{ rasorbs[loop.index0] }}
>> copy $Project.rasscf.molden $backup_path/$Project.rasscf.{{ id_ }}.molden
>> copy $Project.JobIph $backup_path/$Project.{{ id_ }}.JobIph
>> copy $Project.rasscf.h5 $backup_path/$Project.rasscf.{{ id_ }}.h5
{% endif %}

{% if ciroot %}
>> copy $Project.JobIph JOB001
&rassi
 cipr
 mees
>> rm JOB001
>> copy $Project.rassi.h5 $backup_path/$Project.rassi.cas_{{ id_ }}.h5
{% endif %}

{% if caspt2 %}
&caspt2
 imaginary
  0.1
 {% if ciroot %}
 multistate
  {{ ciroot }}{% for i in range(ciroot) %} {{ i+1 }}{% endfor %}
>> copy $Project.JobMix $backup_path/$Project.{{ id_ }}.JobMix
 {% endif %}
{% endif %}


{% if ciroot %}
>> copy $Project.JobMix JOB001
&rassi
 cipr
 ejob
 mees
>> rm JOB001
>> copy $Project.rassi.h5 $backup_path/$Project.rassi.caspt2_{{ id_ }}.h5
{% endif %}

{% if mrci %}
 &mrci
{% endif %}
{% endfor %}
"""
TPL = jinja2.Template(TPL_STR, trim_blocks=True, lstrip_blocks=True)



def parse_args(args):
    parser = argparse.ArgumentParser()

    methods = "hf mp2 cas caspt2 mrci".split()
    parser.add_argument("methods", nargs="+", choices=methods)
    parser.add_argument("backup_path")
    parser.add_argument("--basis", default="cc-pvdz")
    parser.add_argument("--inporb", default=None)
    parser.add_argument("--name", default="job_gen")
    parser.add_argument("--charge", type=int, default=0)
    parser.add_argument("--spin", type=int, default=1)
    parser.add_argument("--ciroot", type=int, default=None)

    return parser.parse_args(args)


def setup_2d_scan(c1_eq, c2_eq):
    coord1_spec = (180, 30, 5)
    coord2_spec = (0.6, 3.5, 0.1)

    def make_coords(start, end, step):
        num = round((abs(start-end)/step) + 1)
        coords = np.linspace(start, end, num)
        return coords, num
    coords1, num1 = make_coords(*coord1_spec)
    coords2, num2 = make_coords(*coord2_spec)

    def ind_from_spec(start, end, step, val):
        return int((val-start)/step * np.sign(end-start))
    c1_eq_ind = ind_from_spec(*coord1_spec, c1_eq)
    c2_eq_ind = ind_from_spec(*coord2_spec, c2_eq)

    """
    ---------------------
    |   up         up   | c2_end
    |   ▲           ▲   |
    |   |           |   |
    | left ◀ eq ▶ right | c2
    |   |           |   |
    |   ▼           ▼   |
    |   down     down   | c2_start
    ---------------------
    c1_start c1   c1_end
    """

    # Coordinates to propagate the INPORB along the row containing the
    # equilibirum geometry from where we start.
    c1_left = coords1[:c1_eq_ind][::-1]
    c1_right = coords1[c1_eq_ind:]
    left_coords = (c1_left, [c2_eq, ])
    right_coords = (c1_right, [c2_eq, ])

    # Coordinates for the up and down directions
    c2_down = coords2[:c2_eq_ind][::-1]
    # Add 1 so we don't include the line with the equilibrium coordinate.
    c2_up = coords2[c2_eq_ind+1:]
    down_coords = (coords1, c2_down)
    up_coords = (coords1, c2_up)

    coords_tuple = (
        ("left", left_coords),
        ("right", right_coords),
        ("down", down_coords),
        ("up", up_coords),
    )
    # return coords_tuple
    return left_coords, right_coords, down_coords, up_coords


def make_zmats(zmat_tpl, id_fmt, coords1, coords2):
    coords_grid = list(it.product(coords1, coords2))
    print("First five internals")
    print(coords_grid[:5])

    ids = [id_fmt.format(c1, c2) for c1, c2 in coords_grid]
    zmats = [zmat_tpl.format(c1=c1, c2=c2) for c1, c2 in coords_grid]

    print("First five Z-Matrices")
    for zm in zmats[:5]:
        print(zm)
    print("...")
    print(f"There are {len(zmats)} Z-Matrices in total.")

    return ids, zmats, coords_grid


def run():
    args = parse_args(sys.argv[1:])

    methods = args.methods
    name = args.name
    backup_path = args.backup_path

    job_kwargs = {
        "basis": args.basis,
        "inporb": args.inporb,
        "charge": args.charge,
        "spin": args.spin,
        "ciroot": args.ciroot,
        "backup_path": args.backup_path,
    }

    for method in methods:
        job_kwargs[method] = True

    if "cas" not in methods:
        job_kwargs["inporb"] = None
    else:
        assert job_kwargs["inporb"], "With cas --inporb must be set!"

    method_str = "_".join(methods)
    print("Using methods:")
    print(" ".join(methods))
    no_print = ("zmats", "ids")
    pprint({k: v for k, v in job_kwargs.items()
            if k not in no_print}
    )

    zmat_tpl = """O1
    H2 1 {c2:.2f}
    H3 1 {c2:.2f} 2 {c1:.1f}"""

    id_fmt = "{:.0f}_{:.1f}"

    c1_eq, c2_eq = 105, 1.0
    coords = setup_2d_scan(c1_eq, c2_eq)

    left_right = [list(it.product(c1, c2)) for c1, c2 in coords[:2]]
    left_right_ids = [id_fmt.format(*cs)
                      for cs in it.chain(left_right[0][::-1], left_right[1])]

    # Generate the RasOrbs that will be used as input for the up
    # and down columns.
    rasorb_fns = lambda ids: [f"{job_kwargs['backup_path']}/{id_}.RasOrb"
                              for id_ in ids]
    eq_rasorbs = rasorb_fns(left_right_ids)

    # Expand the up and down coords into two parts of one row
    jobs = list()
    job_fns = list()
    for coords_name, (coords1, coords2) in zip(("left", "right"), coords[:2]):
        ids, zmats, _ = make_zmats(zmat_tpl, id_fmt, coords1, coords2)
        rasorbs = rasorb_fns(ids)
        job = TPL.render(**job_kwargs,
                         ids=ids,
                         zmats=zmats,
                         rasorbs=rasorbs,
        )
        jobs.append(job)
        fn = f"{coords_name}_{method}_{job_kwargs['basis']}.in"
        job_fns.append(fn)

    # already expand down and up earlier so we can just use one loop for everything?
    # propably not ... 
    # Expand up down into their respective columns
    for coords_name, (coords1, coords2) in zip(("down", "up"), coords[2:]):
        for col, inporb in zip(coords1, eq_rasorbs):
            ids, zmats, _ = make_zmats(zmat_tpl, id_fmt, [col, ], coords2)
            rasorbs = rasorb_fns(ids)
            job_kwargs["inporb"] = inporb
            job = TPL.render(**job_kwargs,
                             ids=ids,
                             zmats=zmats,
                             rasorbs=rasorbs,
            )
            jobs.append(job)
            fn = f"{coords_name}_{col}_{method}_{job_kwargs['basis']}.in"
            job_fns.append(fn)

    for job, fn in zip(jobs, job_fns):
        with open(fn, "w") as handle:
            handle.write(job)
        print(f"Wrote {fn}")

    left_right = jobs_fns[:2]
    cols = jobs_fns[2:]
    import pdb; pdb.set_trace()


if __name__ == "__main__":
    run()
    # c1_eq, c2_eq = 105, 1.0
    # setup_2d_scan(c1_eq, c2_eq)
