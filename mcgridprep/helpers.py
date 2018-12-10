import itertools as it
import re

import numpy as np

from mcgridprep.config import config as CONF


def coords_from_spec(start, end, step):
    num = round((abs(start-end)/step) + 1)
    coords = np.linspace(start, end, num)
    return coords, num


def load_coords():
    coord1_spec = CONF["coord1"]
    coord2_spec = CONF["coord2"]
    coords1, num1 = coords_from_spec(*coord1_spec)
    coords2, num2 = coords_from_spec(*coord2_spec)
    return coords1, num1, coords2, num2


def ind_for_spec(start, end, step, val):
    return int(round((val-start)/step) * np.sign(end-start))


def get_meshgrid(indexing="xy"):
    coord1_spec = CONF["coord1"]
    coord2_spec = CONF["coord2"]
    coords1, _ = coords_from_spec(*coord1_spec)
    coords2, _ = coords_from_spec(*coord2_spec)
    C1, C2 = np.meshgrid(coords1, coords2, indexing=indexing)
    return C1, C2


def id_for_fn_with_type(fn, types):
    float_re = "([-\d\.]+)"
    regex = f"{float_re}_{float_re}\."
    mobj = re.match(regex, str(fn))
    c1, c2 = [t(float(val)) for t, val in zip(types, mobj.groups())]
    return c1, c2


def id_for_fn(fn):
    float_re = "([-\d\.]+)"
    regex = f"{float_re}_{float_re}\."
    mobj = re.match(regex, str(fn))
    c1, c2 = [float(val) for val in mobj.groups()]
    return c1, c2


def id_from_log(text):
    """Parse the ID string ("*# C1_C2 #*") from a log file."""
    float_re = "([\.\d\-]+)"
    id_re = f"\*# {float_re}_{float_re} #\*"
    mobj = re.search(id_re, text)
    return [float(c) for c in mobj.groups()]


def ids_from_log(text):
    float_re = "([\.\d\-]+)"
    id_re = f"\*# {float_re}_{float_re} #\*"
    return [(float(c1), float(c2)) for c1, c2 in re.findall(id_re, text)]
    # doubled_ids = re.findall(id_re, text)
    # unique_ids = doubled_ids[:len(doubled_ids) // 2]
    # return [(float(c1), float(c2)) for c1, c2 in unique_ids]


def get_all_ids():
    coords1, _, coords2, _ = load_coords()
    prod = it.product(coords1, coords2)
    all_ids = [CONF["id_fmt"].format(c1, c2) for c1, c2 in prod]
    return all_ids


def slugify(inp_str):
    inp_str = inp_str.replace("-", "_").replace("(", "").replace(")", "")
    return inp_str
