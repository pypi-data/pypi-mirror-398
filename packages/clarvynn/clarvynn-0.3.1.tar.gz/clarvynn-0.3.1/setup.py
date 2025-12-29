"""
Setup script for Clarvynn.

This setup.py is needed because we have a monorepo structure where:
- core/ contains language-agnostic CPL engine
- adapters/opentelemetry-python/clarvynn/ contains Python OTel integration

We want to package both into a single pip-installable 'clarvynn' package.
"""

import os
import shutil
from pathlib import Path

from setuptools import find_packages, setup

# Read version from pyproject.toml
version = "0.1.0"

# Read long description from README
long_description = (Path(__file__).parent / "README.md").read_text(encoding="utf-8")

# Custom package discovery
packages = []

# 1. Find clarvynn packages in adapters/opentelemetry-python/
for pkg in find_packages("adapters/opentelemetry-python", exclude=["tests*", "examples*"]):
    packages.append(pkg)
    print(f"Found adapter package: {pkg}")

# 2. Find core packages
for pkg in find_packages(".", include=["core*"], exclude=["core.specs*", "core.policies*"]):
    packages.append(pkg)
    print(f"Found core package: {pkg}")

print(f"\nTotal packages to distribute: {packages}")

setup(
    # Metadata is in pyproject.toml, but we need explicit package config here
    name="clarvynn",
    version=version,
    packages=packages,
    package_dir={
        "clarvynn": "adapters/opentelemetry-python/clarvynn",
        "core": "core",
    },
    package_data={
        "": ["*.yaml", "*.yml"],
        "core.policies": ["*.yaml", "*.yml"],
    },
    include_package_data=True,
    zip_safe=False,
)
