# -*- coding: utf-8 -*-

import codecs
import os
import re

from setuptools import setup, find_packages
from pip.req import parse_requirements
from pip.download import PipSession

here = os.path.abspath(os.path.dirname(__file__))


def load_pip_requirements(fp):
    reqs, deps = [], []
    for r in parse_requirements(fp, session=PipSession()):
        if r.url is not None:
            deps.append(str(r.url))
        reqs.append(str(r.req))
    return reqs, deps


# Read the version number from a source file.
# Why read it, and not import?
# see https://groups.google.com/d/topic/pypa-dev/0PkjVpcxTzQ/discussion
def find_version(*file_paths):
    # Open in Latin-1 so that we avoid encoding errors.
    # Use codecs.open for Python 2 compatibility
    with codecs.open(os.path.join(here, *file_paths), 'r', 'latin1') as f:
        version_file = f.read()

    # The version line must have the form
    # __version__ = 'ver'
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


reqs, deps = load_pip_requirements('requirements.txt')

setup(
    name='basketball-standings',
    version=find_version('standings', '__init__.py'),
    description='Command line tool for pulling live basketball standings',

    # The project URL.
    url='http://github.com/clarkperkins/bas',

    # Author details
    author='Clark Perkins',
    author_email='r.clark.perkins@gmail.com',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages.
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),


    dependency_links=deps,

    # List run-time dependencies here.  These will be installed by pip when your
    # project is installed.
    install_requires=reqs,

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={
        'console_scripts': [
            'basketball-standings=standings:main',
        ],
    },
)
