#!/usr/bin/env python3
"""
Setup script for santok_complete package
PyPI Release Configuration
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = ""
if readme_file.exists():
    with open(readme_file, "r", encoding="utf-8") as fh:
        long_description = fh.read()

# Read version from __init__.py
version = "2.0.0"
init_file = Path(__file__).parent / "__init__.py"
if init_file.exists():
    with open(init_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("__version__"):
                version = line.split("=")[1].strip().strip('"').strip("'")
                break

setup(
    name="santok",
    version=version,
    author="Santosh Chavala",
    author_email="chavalasantosh@example.com",
    description="Comprehensive Text Processing System: Tokenization, Embeddings, Training, Vector Stores, and More",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/chavalasantosh/SanTOK",
    project_urls={
        "Bug Reports": "https://github.com/chavalasantosh/SanTOK/issues",
        "Source": "https://github.com/chavalasantosh/SanTOK",
        "Documentation": "https://github.com/chavalasantosh/SanTOK/tree/main/santok_complete",
    },
    packages=find_packages(where=".", exclude=["tests", "tests.*", "examples", "examples.*"]),
    package_dir={"": "."},
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires=">=3.7",
    install_requires=[
        # Core dependencies (add as needed)
        # "numpy>=1.19.0",
        # "tensorflow>=2.0.0",  # If using embeddings/training
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
        ],
    },
    entry_points={
        "console_scripts": [
            "santok=santok_complete.cli.cli:main",
        ],
    },
)
