"""Setup configuration for PyIoneer."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

setup(
    name="pyioneer",
    version="0.1.0",
    description="A Python library for idealizing single-channel current recordings",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Adam Dorey",
    author_email="adamdorey92@gmail.com",
    url="https://github.com/Adorey92-git/pyioneer",
    packages=find_packages(),
    install_requires=[
        "pyabf>=2.3.8",
        "numpy>=1.24.0",
        "scipy>=1.10.0",
        "click>=8.0.0",
    ],
    extras_require={
        "hmm": ["hmmlearn>=0.2.7"],
        "changepoint": ["ruptures>=1.1.8"],
        "all": ["hmmlearn>=0.2.7", "ruptures>=1.1.8", "pandas>=2.0.0"],
    },
    entry_points={
        "console_scripts": [
            "pyioneer=pyioneer.cli:cli",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
)

