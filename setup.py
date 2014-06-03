#!/usr/bin/env python

from setuptools import find_packages, setup

long_description = """Basic tree node implementation.
"""

appname = "treebie"
version = "0.00"

setup(**{
    "name": appname,
    "version": version,
    "packages": [
        'tater',
        ],
    "author": "Thom Neale",
    "packages": find_packages(exclude=['tests*']),
    "author_email": "twneale@gmail.com",
    "long_description": long_description,
    "description": 'Basic tree node implementation',
    "license": "MIT",
    "url": "http://twneale.github.com/treebie/",
    "platforms": ['any'],
    "scripts": [
    ]
})
