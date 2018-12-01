#!/usr/bin/env python3

import itertools as it
from pathlib import Path
from pprint import pprint
import sys
import textwrap

import jinja2
import numpy as np

from mcgridprep.config import config as CONF
from mcgridprep.helpers import coords_from_spec, ind_for_spec


TPL_STR = """
>> export backup_path={{ backup_path }}
{% if inporb %}
>> copy {{ inporb }} $Project.RasOrb
{% endif %}

{% for id_ in ids %}
&gateway
{% if zmats %}
xbas
  {{ basis }}
 zmat
  {{ zmats[loop.index0] }}
 end of zmat
{% endif %}
{% if xyzs %}
 coord
  {{ xyzs[loop.index0] }}
 basis
  {{ basis }}
 group
  nosym
{% endif %}
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
>> copy $Project.RasOrb $backup_path/{{ id_ }}.RasOrb
>> copy $Project.rasscf.molden $backup_path/{{ id_ }}.rasscf.molden
>> copy $Project.JobIph $backup_path/{{ id_ }}.JobIph
>> copy $Project.rasscf.h5 $backup_path/{{ id_ }}.rasscf.h5
{% endif %}

{% if ciroot %}
>> copy $Project.JobIph JOB001
&rassi
 cipr
 mees
>> rm JOB001
>> copy $Project.rassi.h5 $backup_path/{{ id_ }}.rassi_cas.h5
{% endif %}

{% if caspt2 %}
&caspt2
 imaginary
  0.1
 {% if ciroot %}
 multistate
  {{ ciroot }}{% for i in range(ciroot) %} {{ i+1 }}{% endfor %}

>> copy $Project.JobMix $backup_path/{{ id_ }}.JobMix
 {% endif %}
{% endif %}


{% if ciroot %}
>> copy $Project.JobMix JOB001
&rassi
 cipr
 ejob
 mees
>> rm JOB001
>> copy $Project.rassi.h5 $backup_path/{{ id_ }}.rassi_pt2.h5
{% endif %}

{% endfor %}
"""
TPL = jinja2.Template(TPL_STR, trim_blocks=True, lstrip_blocks=True)


def setup_2d_scan(coord1_spec, coord2_spec, c_eq):
    c1_eq, c2_eq = c_eq

    coords1, num1 = coords_from_spec(*coord1_spec)
    coords2, num2 = coords_from_spec(*coord2_spec)

    c1_eq_ind = ind_for_spec(*coord1_spec, c1_eq)
    c2_eq_ind = ind_for_spec(*coord2_spec, c2_eq)

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

    # Coordinates to propagate the INPORB along one row. We start at some
    # geometry, propably the equilibrium geometry. From the starting point
    # we propagate the INPORB to the left and to the right in two
    # calculations.
    c1_left = coords1[:c1_eq_ind][::-1]
    c1_right = coords1[c1_eq_ind:]
    left_coords = (c1_left, [c2_eq, ])
    right_coords = (c1_right, [c2_eq, ])

    # After propagating the INPORB along one row, we can set up a separate
    # job for every column. Starting from the first row, we will set up the
    # coordinates for two directions. Down and up.
    c2_down = coords2[:c2_eq_ind][::-1]
    # Add 1 so we don't include the line with the equilibrium coordinate,
    # as it was already calculated in the left/right calculation.
    c2_up = coords2[c2_eq_ind+1:]
    down_coords = (coords1, c2_down)
    up_coords = (coords1, c2_up)

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


def make_xyz(angle, bond):
    beta = angle/2
    alpha = 90 - beta

    sina = np.sin(np.deg2rad(alpha))
    sinb = np.sin(np.deg2rad(beta))
    a = sina * bond
    b = sinb * bond

    xyz = f"""3

    O  0.00000000  0.00000000  0.00000000
    H  0.00000000  {b:.8f}  {a:.8f}
    H  0.00000000  {-b:.8f} {a:.8f}"""
    return textwrap.dedent(xyz)


def make_xyzs(id_fmt, coords1, coords2):
    coords_grid = list(it.product(coords1, coords2))
    # print("First five internals")
    # print(coords_grid[:5])

    ids = [id_fmt.format(c1, c2) for c1, c2 in coords_grid]
    xyzs = [make_xyz(angle=c1, bond=c2) for c1, c2 in coords_grid]

    # print("First five .xyz-files")
    # for xyz in xyzs[:5]:
        # print(xyz)
    # print("...")
    # print(f"There are {len(xyzs)} .xyz files in total.")

    return ids, xyzs, coords_grid


def run():
    print("Job configuration")
    pprint(CONF)

    methods = CONF["methods"]
    name = CONF["name"]
    backup_path = Path(CONF["backup_path"]).resolve()
    job_kwargs = {
        "basis": CONF["basis"],
        "charge": CONF["charge"],
        "spin": CONF["spin"],
        "ciroot": CONF["ciroot"],
        "backup_path": backup_path,
    }

    for method in methods:
        job_kwargs[method] = True

    if "cas" not in methods:
        inporb = None
    else:
        inporb = Path(CONF["inporb"]).resolve()
    job_kwargs["inporb"] = inporb

    method_str = "_".join(methods)
    # print("Using methods:")
    # print(" ".join(methods))
    no_print = ("zmats", "ids")
    # pprint({k: v for k, v in job_kwargs.items()
            # if k not in no_print}
    # )

    zmat_tpl = """O1
    H2 1 {c2:.2f}
    H3 1 {c2:.2f} 2 {c1:.1f}"""

    id_fmt = "{:.0f}_{:.1f}"

    coord1_spec = CONF["coord1"]
    coord2_spec = CONF["coord2"]
    c_eq = CONF["coord_eq"]
    coords = setup_2d_scan(coord1_spec, coord2_spec, c_eq)

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
        # ids, zmats, _ = make_zmats(zmat_tpl, id_fmt, coords1, coords2)
        ids, xyzs, _ = make_xyzs(id_fmt, coords1, coords2)
        job = TPL.render(**job_kwargs,
                         ids=ids,
                         # zmats=zmats,
                         xyzs=xyzs,
        )
        jobs.append(job)
        fn = f"{coords_name}_{method}_{job_kwargs['basis']}.in"
        job_fns.append(fn)

    # Expand up down into their respective columns
    for coords_name, (coords1, coords2) in zip(("down", "up"), coords[2:]):
        for col, inporb in zip(coords1, eq_rasorbs):
            # ids, zmats, _ = make_zmats(zmat_tpl, id_fmt, [col, ], coords2)
            ids, xyzs, _ = make_xyzs(id_fmt, [col, ], coords2)
            # To set up the columns we use the RasOrbs from the equilibrium row.
            job_kwargs["inporb"] = inporb
            job = TPL.render(**job_kwargs,
                             ids=ids,
                             # zmats=zmats,
                             xyzs=xyzs,
            )
            jobs.append(job)
            fn = f"{coords_name}_{col}_{method}_{job_kwargs['basis']}.in"
            job_fns.append(fn)

    for job, fn in zip(jobs, job_fns):
        with open(fn, "w") as handle:
            handle.write(job)
        # print(f"Wrote {fn}")

    job_inputs_fn = "job_inputs"
    with open(job_inputs_fn, "w") as handle:
        handle.write("\n".join(job_fns))
    print(f"Wrote list of all job inputs to '{job_inputs_fn}'")


if __name__ == "__main__":
    run()
    # c1_eq, c2_eq = 105, 1.0
    # setup_2d_scan(c1_eq, c2_eq)
