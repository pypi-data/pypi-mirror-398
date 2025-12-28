# -*- coding: utf-8 -*-
"""
:Author: ChenXiaolei
:Date: 2020-04-22 21:25:59
:LastEditTime: 2025-12-25 10:34:36
:LastEditors: ChenXiaolei
:Description: 
"""
from __future__ import print_function
from setuptools import setup, find_packages

with open("README.md", "r", encoding='utf-8') as fh:
    long_description = fh.read()

setup(
    name="rocket_hub",
    version="1.0.1b1",
    author="rocket_man",
    author_email="rocket@ggo9.com",
    description="rocket hub",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    url="https://gitee.com/rocket_man/rocket_framework",
    packages=find_packages(),
    install_requires=[
        "rocket-framework",
        "asq>=1.3"
    ],
    classifiers=[
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
    ],
    python_requires='~=3.4',
)