#!/usr/bin/env python3
"""
Setup configuration for epochcore-quantum-decision Python package
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="epochcore-quantum-decision",
    version="1.0.0",
    author="John Vincent Ryan",
    author_email="john@epochcore.com",
    description="Quantum decision system with 7 oscillations and golden ratio harmonics",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/epochcore/quantum-decision-python",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Physics",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        # No external dependencies - pure Python implementation
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0",
            "mypy>=1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "quantum-decision=epoch_quantum_decision:main",
        ],
    },
    keywords="quantum decision golden-ratio oscillation cryptography trading fintech trinity-architecture",
    project_urls={
        "Bug Reports": "https://github.com/epochcore/quantum-decision-python/issues",
        "Source": "https://github.com/epochcore/quantum-decision-python",
        "Documentation": "https://github.com/epochcore/quantum-decision-python#readme",
    },
    include_package_data=True,
    zip_safe=False,
)
