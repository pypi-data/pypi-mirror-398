# -*- coding: utf-8 -*-
"""
:Author: HuangJianYi
:Date: 2020-04-22 21:25:59
:LastEditTime: 2024-08-06 15:38:56
:LastEditors:  HuangJianYi
:Description: 
"""
from __future__ import print_function
from setuptools import setup, find_packages

with open("README.md", "r", encoding='utf-8') as fh:
    long_description = fh.read()

setup(
    name="hk_cdp",
    version="1.0.130",
    author="seven",
    author_email="tech@gao7.com",
    description="hk cdp",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    url="http://gitlab.tdtech.gao7.com/newfire/hk_cap/hk_cdp/server/hk_cdp.git",
    packages=find_packages(),
    install_requires=[
        "seven-framework >=1.1.51"
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
    ],
    python_requires='~=3.4',
)