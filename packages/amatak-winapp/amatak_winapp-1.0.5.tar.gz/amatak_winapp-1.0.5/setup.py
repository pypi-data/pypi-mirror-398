#!/usr/bin/env python3
from setuptools import setup, find_packages
import os

# Read the contents of README.md
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read version from amatak_winapp/data/VERSION.txt
version_file = os.path.join("amatak_winapp", "data", "VERSION.txt")
if os.path.exists(version_file):
    with open(version_file, "r", encoding="utf-8") as fh:
        version = fh.read().strip()
else:
    version = "1.0.2"

# Read requirements
requirements = []
if os.path.exists("requirements.txt"):
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="amatak-winapp",
    version=version,
    author="Amatak Development Team",
    author_email="amatak.io@outlook.com",
    description="A Python toolkit for creating Windows application installers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/amatak-org/amatak_winapp",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'amatak_winapp': [
            'data/*.txt',
            'assets/brand/*',
            'gui/*.py',
            'scripts/*.py',
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "winapp=amatak_winapp.winapp:main",
        ],
    },
    keywords=[
        "windows",
        "installer", 
        "nsis",
        "pyinstaller",
        "packaging",
    ],
    project_urls={
        "Bug Reports": "https://github.com/amatak-org/amatak_winapp/issues",
        "Source": "https://github.com/amatak-org/amatak_winapp",
    },
)