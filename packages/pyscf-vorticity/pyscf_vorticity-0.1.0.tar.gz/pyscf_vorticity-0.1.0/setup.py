"""
pyscf-vorticity: Geometric correlation analysis for quantum chemistry
"""

import os
from setuptools import setup, find_packages

# README があれば読む
long_description = ""
if os.path.exists("README.md"):
    with open("README.md", "r", encoding="utf-8") as f:
        long_description = f.read()

setup(
    name="pyscf-vorticity",
    version="0.1.0",
    author="Masamichi Iizumi",
    author_email="m.iizumi@miosync.email",
    description="Λ³-DFT: Vorticity-based exchange-correlation analysis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/miosync-masa/pyscf-vorticity",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.20",
        "scipy>=1.7",
    ],
    extras_require={
        "pyscf": ["pyscf>=2.0"],
        "jax": ["jax>=0.4", "jaxlib>=0.4"],
        "full": ["pyscf>=2.0", "jax>=0.4", "jaxlib>=0.4"],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Chemistry",
        "Topic :: Scientific/Engineering :: Physics",
    ],
    keywords="DFT, quantum chemistry, correlation, vorticity",
)
