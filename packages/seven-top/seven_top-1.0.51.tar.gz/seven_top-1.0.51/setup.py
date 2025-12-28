# -*- coding: utf-8 -*-
"""
@Author: HuangJingCan
@Date: 2020-04-22 21:25:59
@LastEditTime: 2022-07-27 14:42:39
@LastEditors: HuangJianYi
@Description: 
"""
from __future__ import print_function
from setuptools import setup, find_packages

with open("README.md", "r", encoding='utf-8') as fh:
    long_description = fh.read()

setup(
    name="seven_top",
    version="1.0.51",
    author="seven",
    author_email="tech@gao7.com",
    description="seven top",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    url="http://gitlab.tdtech.gao7.com/TaoBaoCloud/seven_top.git",
    packages=find_packages(),
    install_requires=[
        "oss2 >= 2.13.0"
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
    ],
    python_requires='~=3.4',
)
