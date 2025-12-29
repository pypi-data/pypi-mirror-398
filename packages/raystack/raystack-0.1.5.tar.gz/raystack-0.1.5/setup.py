#!/usr/bin/env python
"""Setup script for raystack."""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            return f.read()
    return "Starlette sizzles, Django dazzles. The best of both worlds in one framework."

setup(
    name="raystack",
    version="0.0.0",
    description="Starlette sizzles, Django dazzles. The best of both worlds in one framework.",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="Vladimir Penzin",
    author_email="pvenv@icloud.com",
    url="https://github.com/ForceFledgling/raystack",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.6",
    # Dependencies are defined in pyproject.toml
    # install_requires is automatically read from pyproject.toml
    entry_points={
        "console_scripts": [
            "raystack=raystack.core.management:execute_from_command_line",
        ],
    },
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Web Environment",
        "Framework :: Starlette",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    # License is defined in pyproject.toml
)
