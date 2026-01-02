#!/usr/bin/env python
"""
UniVersCell - Production-ready constraint primitives language
Setup for PyPI distribution
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="universcell",
    version="1.0.0",
    description="Production-ready constraint primitives language with 15 core types",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="UniVersCell Team",
    author_email="dev@universcell.io",
    url="https://github.com/universcell/universcell",
    license="MIT",
    packages=find_packages(include=["universalengine", "universalengine.*"]),
    python_requires=">=3.8",
    install_requires=[
        "dataclasses-json>=0.5.7",
        "pydantic>=1.10.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.12",
            "black>=21.0",
            "mypy>=0.910",
        ],
        "docs": [
            "sphinx>=4.0",
            "sphinx-rtd-theme>=1.0",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Distributed Computing",
    ],
    keywords=[
        "constraints",
        "primitives",
        "distributed",
        "decision-making",
        "governance",
        "framework",
    ],
    project_urls={
        "Bug Tracker": "https://github.com/universcell/universcell/issues",
        "Documentation": "https://universcell.readthedocs.io",
        "Source Code": "https://github.com/universcell/universcell",
    },
    include_package_data=True,
    zip_safe=False,
)
