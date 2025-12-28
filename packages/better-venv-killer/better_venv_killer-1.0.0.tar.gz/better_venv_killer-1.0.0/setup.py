#!/usr/bin/env python3
"""
Setup script for venv-killer package
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8') if (this_directory / "README.md").exists() else ""

setup(
    name="better-venv-killer",
    version="1.0.0",
    author="holygrimmdev",  # TODO: Replace with your actual name
    author_email="abhaygp18.dev@gmail.com",  # TODO: Replace with your actual email
    description="Find and delete Python virtual environments to free disk space",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/darkbits018",  # TODO: Replace with your actual GitHub URL
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Environment :: X11 Applications",
    ],
    python_requires=">=3.7",
    install_requires=[
        # No external dependencies - uses only standard library
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black",
            "flake8",
        ],
    },
    entry_points={
        "console_scripts": [
            "better-venv-killer=venv_killer.cli:main",
            "better-venv-killer-gui=venv_killer.gui:main",
        ],
    },
    keywords="virtual environment venv conda cleanup disk space developer tools",
    project_urls={
        "Bug Reports": "https://github.com/darkbits018/better-venv-killer/issues",
        "Source": "https://github.com/darkbits018/better-venv-killer",
    },
)