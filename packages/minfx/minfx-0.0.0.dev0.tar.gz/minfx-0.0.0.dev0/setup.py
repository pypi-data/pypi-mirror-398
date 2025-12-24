#!/usr/bin/env python3
"""
Setup script for MinFX package.
"""

from setuptools import setup, find_packages
import os


# Read the README file for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


# Read version from VERSION file
def get_version():
    version_path = os.path.join(os.path.dirname(__file__), "VERSION")
    with open(version_path, "r", encoding="utf-8") as f:
        return f.read().strip()


setup(
    name="minfx",
    version=get_version(),
    author="Minfx Team",
    author_email="team@minfx.ai",
    description="A minimal Python package for the Minfx project",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/minfx-ai/minfx",
    project_urls={
        "Bug Reports": "https://github.com/minfx-ai/minfx/issues",
        "Source": "https://github.com/minfx-ai/minfx",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "neptune",
        "neptune-scale",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
