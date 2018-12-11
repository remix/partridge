#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""
import io

from setuptools import setup, find_packages

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

# About dict to store version and package info
about = dict()
with io.open("partridge/__version__.py", "r", encoding="utf-8") as f:
    exec(f.read(), about)

requirements = [
    "cchardet",
    'functools32;python_version<"3"',
    "networkx>=2.0",
    "pandas",
    "isoweek",
]

setup_requirements = ["pytest-runner"]

test_requirements = ["black", "flake8", "pytest"]

setup(
    name="partridge",
    version=about["__version__"],
    description="Partridge is python library for working with GTFS "
    "feeds using pandas DataFrames.",
    long_description=readme + "\n\n" + history,
    author="Danny Whalen",
    author_email="daniel.r.whalen@gmail.com",
    url="https://github.com/remix/partridge",
    packages=find_packages(include=["partridge"]),
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords="partridge",
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
    ],
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, <4",
    test_suite="tests",
    tests_require=test_requirements,
    setup_requires=setup_requirements,
)
