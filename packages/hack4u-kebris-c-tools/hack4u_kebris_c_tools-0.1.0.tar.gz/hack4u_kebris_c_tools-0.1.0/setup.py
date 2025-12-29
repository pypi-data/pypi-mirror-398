#!/usr/bin/env python3

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
        name="hack4u-kebris-c-tools",
        version="0.1.0",
        packages=find_packages(),
        install_requires=[],
        author="kebris-c",
        description="A library to list courses from Hack4u web",
        long_description=long_description,
        long_description_content_type="text/markdown",
        url="https://hack4u.io"
        )
