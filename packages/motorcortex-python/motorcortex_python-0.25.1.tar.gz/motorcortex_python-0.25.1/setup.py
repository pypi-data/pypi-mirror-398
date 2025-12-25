#!/usr/bin/python3

#
#   Developer: Alexey Zakharov (alexey.zakharov@vectioneer.com)
#   All rights reserved. Copyright (c) 2020 VECTIONEER.
#


from setuptools import setup
import os

with open("README.md", "r") as fh:
    long_description = fh.read()


def read_version():
    version_file = os.path.join(os.path.dirname(__file__), "motorcortex", "version.py")
    with open(version_file) as f:
        for line in f:
            if line.startswith("__version__"):
                delim = '"' if '"' in line else "'"
                return line.split(delim)[1]
    raise RuntimeError("Unable to find version string.")


setup(name='motorcortex-python',
      version=read_version(),
      description='Python bindings for Motorcortex Engine',
      long_description=long_description,
      long_description_content_type="text/markdown",
      author='Alexey Zakharov',
      author_email='alexey.zakharov@vectioneer.com',
      url='https://www.motorcortex.io',
      license='MIT',
      packages=['motorcortex'],
      install_requires=['pynng==0.8.*',
                        'protobuf>=3.20'],
      include_package_data=True,
      )
