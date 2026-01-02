#!/usr/bin/env python
"""
Universell Cell Framework - Production governance framework
Setup for PyPI distribution
"""

from setuptools import setup
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="universcell-framework",
    version="1.0.0",
    description="Enterprise governance framework with 7 adoption patterns",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Universell Framework Team",
    author_email="framework@universcell.io",
    url="https://github.com/universcell/framework",
    license="MIT",
    py_modules=[
        "PHASE7_ERROR_HANDLING",
        "PHASE7_MONITORING",
        "PHASE7_SECURITY",
        "PHASE7_ALERTING",
    ],
    python_requires=">=3.8",
    install_requires=[
        "dataclasses-json>=0.5.7",
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Networking",
        "Topic :: System :: Systems Administration",
    ],
    keywords=[
        "framework",
        "governance",
        "kubernetes",
        "ci-cd",
        "database",
        "finance",
        "error-handling",
        "monitoring",
        "security",
        "alerting",
    ],
    project_urls={
        "Bug Tracker": "https://github.com/universcell/framework/issues",
        "Documentation": "https://framework.universcell.io",
        "Source Code": "https://github.com/universcell/framework",
    },
)
