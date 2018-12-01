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
}

def load_yaml():
    yaml_fn = "mcgrid.yaml"
    look_in_dirs = [".", ".."]

    paths = [Path(dir_) / yaml_fn for dir_ in look_in_dirs]
    yaml_path = [p for p in paths if p.is_file()][0]
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
