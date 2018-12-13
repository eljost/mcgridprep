#!/usr/bin/env python3

from setuptools import setup, find_packages
import sys

if sys.version_info.major < 3:
    raise SystemExit("Python 3 is required!")

setup(
    name="mcgridprep",
    version="0.4.3",
    description="Prepare/run 2D grids using OpenMolcas.",
    url="https://github.com/eljost/mcgridprep",
    maintainer="Johannes Steinmetzer",
    maintainer_email="johannes.steinmetzer@uni-jena.de",
    license="GPL 3",
    platforms=["unix"],
    packages=find_packages(),
    package_data={"mcgridprep": ["templates/*.tpl", ],},
    install_requires=[
        "numpy",
        "jinja2",
        "h5py",
        "pyyaml",
    ],
    entry_points={
        "console_scripts": [
            "mcgridprep = mcgridprep.main:run",
            "mcgridrun = mcgridprep.run:run",
            "mcgridparse = mcgridprep.parse:run",
            "mcgridplot = mcgridprep.plot:run",
            "dalgrid = mcgridprep.dalgrid:run",
            "dalparse = mcgridprep.dalparse:run",
            "dalplot = mcgridprep.dalplot:run",
        ]
    },
)
