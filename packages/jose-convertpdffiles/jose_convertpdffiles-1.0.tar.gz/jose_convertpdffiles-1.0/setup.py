import setuptools
from pathlib import Path

setuptools.setup(
    name="jose_convertpdffiles",
    version=1.0,
    long_description=Path("README.md").read_text(),
    # This line at the end use an array to exclude test and data directories because we don't have python files
    packages=setuptools.find_packages(exclude=["test", "data"])
)
