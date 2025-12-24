"""Setup script for internacia SDK."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="internacia",
    version="0.2.0",
    description="Python SDK for accessing internacia-db data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Dateno",
    license="MIT",
    python_requires=">=3.8",
    packages=find_packages(),
    install_requires=[
        "duckdb>=0.9.0",
        "pandas>=2.0.0",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)

