#!/usr/bin/env python3

from setuptools import setup, find_packages
import sys

if sys.version_info.major < 3:
    raise SystemExit("Python 3 is required!")

setup(
    name="mcgridprep",
    version="0.1",
    description="Prepare/run 2D grids using OpenMolcas.",
    url="https://github.com/eljost/mcgridprep",
    maintainer="Johannes Steinmetzer",
    maintainer_email="johannes.steinmetzer@uni-jena.de",
    license="GPL 3",
    platforms=["unix"],
    packages=find_packages(),
    install_requires=[
        "numpy",
        "jinja2",
    ],
    entry_points={
        "console_scripts": [
            "mcgridprep = mcgridprep.main:run",
            "mcgridrun = mcgridprep.run:run",
        ]
    },
)
