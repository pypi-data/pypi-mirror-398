#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re

from setuptools import setup

PACKAGE = "finalsa-dynamo-dao"
URL = "https://github.com/finalsa/finalsa-dynamo-dao"
PACKAGE_FOLDER = "finalsa/dynamo/dao"

def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    with open(os.path.join(package, "__init__.py")) as f:
        return re.search("__version__ = ['\"]([^'\"]+)['\"]", f.read()).group(1)


def get_long_description():
    """
    Return the README.
    """
    with open("README.md", encoding="utf8") as f:
        return f.read()


def get_packages(package):
    """
    Return root package and all sub-packages.
    """
    return [
        dirpath
        for dirpath, dirnames, filenames in os.walk(package)
        if os.path.exists(os.path.join(dirpath, "__init__.py"))
    ]


setup(
    name=PACKAGE,
    version=get_version(PACKAGE_FOLDER),
    url=URL,
    license="MIT",
    description="An utils package for using dynamodb",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    keywords=[
        "dynamodb",
    ],
    author="Luis Jimenez",
    author_email="luis@finalsa.com",
    packages=get_packages(PACKAGE_FOLDER),
    package_data={PACKAGE: ["py.typed"]},
    include_package_data=True,
    zip_safe=True,
    python_requires=">=3.10",
    data_files=[("", ["LICENSE.md"])],
    install_requires=[
        "boto3>=1.20.3"
    ],
    extras_require={
    
    },
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Topic :: Internet :: WWW/HTTP",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
