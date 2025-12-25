from setuptools import setup, find_packages
from os import path

name = "loggez"
version = "0.6.0"
description = "Python Easy Logging (LOGG EZ)"
url = "https://gitlab.com/meehai/loggez"

loc = path.abspath(path.dirname(__file__))
with open(f"{loc}/README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

required = ["colorama>=0.4.6"]

setup(
    name=name,
    version=version,
    description=description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=url,
    packages=find_packages(),
    install_requires=required,
    dependency_links=[],
    license="WTFPL",
    python_requires=">=3.8"
)
