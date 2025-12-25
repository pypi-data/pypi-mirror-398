"""Setup configuration for mpl-richtext package."""

from setuptools import setup, find_packages
import os

# Read version from version.py
version = {}
with open(os.path.join("mpl_richtext", "version.py")) as f:
    exec(f.read(), version)

# Read README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mpl-richtext",
    version=version['__version__'],
    author="Rabin Katel",
    author_email="kattelrabinraja13@gmail.com",
    description="Rich text rendering for Matplotlib with multi-color, mutli(fonts size, font family, font weight) and multi-style support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ra8in/mpl-richtext",
    project_urls={
        "Bug Tracker": "https://github.com/ra8in/mpl-richtext/issues",
        "Documentation": "https://github.com/ra8in/mpl-richtext#readme",
        "Source Code": "https://github.com/ra8in/mpl-richtext",
    },
    packages=find_packages(exclude=["tests", "examples", "docs"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Visualization",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "matplotlib>=3.5.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "black>=22.0",
            "flake8>=5.0",
            "mypy>=0.990",
        ],
    },
    keywords=[
        "matplotlib",
        "text",
        "color",
        "rich-text",
        "multi-color",
        "visualization",
        "plotting",
    ],
    license="MIT",
)