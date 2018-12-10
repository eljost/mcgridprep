#!/usr/bin/env python3

import os

from jinja2 import Environment, FileSystemLoader, Template

THIS_DIR = os.path.dirname(os.path.realpath(__file__))
ENV = Environment(
        loader=FileSystemLoader([
                os.path.join(THIS_DIR, "templates"),
        ]),
        trim_blocks=True, lstrip_blocks=True 
)
