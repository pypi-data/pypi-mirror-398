import os
import sys
import pathlib
from setuptools import setup, find_packages, find_namespace_packages

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# Version: major.minor.patch
VERSION = (HERE / "VERSION").read_text().strip()

# License
LICENSE = 'CC BY-NC-SA 4.0'

# Required Python version
PYTHON_VERSION = '>= 3.4'


setup \
    ( name             = "pynsi"
    , version          = VERSION
    , description      = "NSI2000 Professional Antenna Measurement Software Automation Module"
    , long_description = README
    , long_description_content_type='text/markdown'
    , license          = LICENSE
    , author           = "Hüseyin YİĞİT"
    , author_email     = "yigit.hsyn@gmail.com"
    , install_requires = \
        [ 'pywin32' ]
    , packages         = find_namespace_packages(where='src'),
      package_dir      = {"": "src"}
    , platforms        = 'Any'
    , url              = "https://github.com/yigithsyn/pynsi"
    , python_requires  = PYTHON_VERSION
    , classifiers      = \
        [ 'Development Status :: 2 - Pre-Alpha'
        # , 'License :: OSI Approved :: ' + LICENSE
        , 'Operating System :: OS Independent'
        , 'Programming Language :: Python'
        , 'Programming Language :: Python :: 3'
        , 'Intended Audience :: Science/Research'
        , 'Topic :: Scientific/Engineering'
        , 'Topic :: Scientific/Engineering :: Mathematics'
        , 'Topic :: Scientific/Engineering :: Physics'
        ]
    )
