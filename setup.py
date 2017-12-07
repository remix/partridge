#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""
import sys
from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

# About dict to store version and package info
about = dict()
if sys.version_info[0] >= 3:
    with open('partridge/__version__.py', 'r', encoding='utf-8') as f:
        exec(f.read(), about)
else:
    with open('partridge/__version__.py', 'r') as f:
        exec(f.read().decode('utf-8'), about)

requirements = [
    'networkx>=2.0',
    'pandas',
]

setup_requirements = [
    'pytest-runner',
]

test_requirements = [
    'pytest',
]

setup(
    name='partridge',
    version=about['__version__'],
    description='Partridge is python library for working with GTFS feeds using pandas DataFrames.',
    long_description=readme + '\n\n' + history,
    author='Danny Whalen',
    author_email='daniel.r.whalen@gmail.com',
    url='https://github.com/remix/partridge',
    packages=find_packages(include=['partridge']),
    include_package_data=True,
    install_requires=requirements,
    license='MIT license',
    zip_safe=False,
    keywords='partridge',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    setup_requires=setup_requirements,
)
