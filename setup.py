"""
@Author: Rossi
2016-02-01
"""
import os.path
from re import VERBOSE
from setuptools import setup, find_packages

dependency_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
with open(dependency_file) as fi:
    dependencies = [line.strip() for line in fi]

version_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "VERSION")
with open(version_file) as fi:
    version = fi.read().strip()


setup(
    name="time_extraction",
    version=version,
    description="time expression extraction and normalization tool",
    author="Rossi",
    packages=find_packages(exclude=("test", "test.*")),
    install_requires=dependencies,
)
