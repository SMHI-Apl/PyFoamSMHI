#!/usr/bin/env python
# -*- coding: us-ascii -*-
"""Build and install the PyFoamSMHI package."""

from ez_setup import use_setuptools
use_setuptools()

import sys

from setuptools import setup, find_packages

install_requires = ['PyFoam>=0.6.1']
tests_require = []
if sys.version_info < (2, 7):
    # pull in some Python 2.7 specific features for 2.6
    install_requires.extend(['argparse'])
    tests_require.extend(['unittest2==0.5.1'])

setup(
    name='PyFOAMSMHI',
    version='0.1',
    author='David Segersson',
    author_email='david.segersson@smhi.se',
    description='A Python package for easy manipulation of OpenFOAM cases in an SMHI environment',
    url='https://github.com/dsegerss/PyFoamSMHI',
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'windRunner = PyFoamSMHI.tools.windRunner:main',
            'speciesRunner = PyFoamSMHI.tools.speciesRunner:main',
            'setWdir = PyFoamSMHI.tools.setWdir:main',
            'archiveToRuntime = PyFoamSMHI.tools.archiveToRuntime:main',
            'batchRun = PyFoamSMHI.tools.batchRun:main',
        ],
    },
    setup_requires=['setuptools_git'],
    install_requires=install_requires,

    tests_require=tests_require,
    test_suite='PyFoamSMHI.tests',
)
