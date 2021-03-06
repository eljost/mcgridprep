#!/usr/bin/env python3

import copy
import logging
from pathlib import Path
import sys

import yaml

DEFAULTS = {
    "ciroot": None,
    "name": None,
    "inporb": None,
    "id_fmt": "{:.2f}_{:.2f}",
    "coord1_lbl": "",
    "coord2_lbl": "",
    "delta": 0.001,
    # Dalton
    "dal_sym": False,
    "dal_generators": "",
    "dal_reuse": None,
}

def load_yaml():
    yaml_fn = "mcgrid.yaml"
    look_in_dirs = [".", ".."]

    paths = [Path(dir_) / yaml_fn for dir_ in look_in_dirs]
    yaml_paths = [p for p in paths if p.is_file()]
    if len(yaml_paths) == 0:
        print("Couldn't find '{yaml_fn}'. Exiting!")
    yaml_path = yaml_paths[0]
    print(f"Using parameters from '{yaml_path}'")

    try:
        with open(yaml_path) as handle:
            from_yaml = yaml.load(handle)
    except:
        logging.exception(f"Tried to read parameters from '{yaml_fn}' "
                           "but something went wrong. Exiting!")
        sys.exit()

    config_copy = DEFAULTS.copy()
    config_copy.update(from_yaml)
    return config_copy

config = load_yaml()
