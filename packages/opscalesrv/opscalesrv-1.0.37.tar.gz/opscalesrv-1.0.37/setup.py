#!/usr/bin/env python3
"""
Setup script for opscalesrv package
"""

from setuptools import setup, find_packages
import os

# Read requirements from requirements.txt and README.md
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'requirements.txt'), encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

# Read README.md for long description
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="opscalesrv",
    version="1.0.37",
    author="opriori - Altay Kirecci",
    author_email="altay.kirecci@gmail.com",
    description="Serial Port Reader HTTP Service with ABAP integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/altaykireci/serialsrv",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Hardware :: Hardware Drivers",
        "Topic :: System :: Networking",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "opscalesrv=opscalesrv:main",
        ],
    },
    include_package_data=True,
    package_data={
        "opscalesrv": [
            "abap/*.abap",
            "*.json",
        ],
    },
    keywords="serial, http, server, abap, sap, iot, arduino, sensor",
    project_urls={
        "Bug Reports": "https://github.com/altaykireci/serialsrv/issues",
        "Source": "https://github.com/altaykireci/serialsrv",
        "Documentation": "https://github.com/altaykireci/serialsrv#readme",
    },
)
