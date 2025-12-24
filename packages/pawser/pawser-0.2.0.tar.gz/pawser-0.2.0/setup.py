from setuptools import setup, find_packages
from pathlib import Path

# Read the README.md for long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="pawser",                      # Your project name on PyPI
    version="0.2.0",                    # Current version
    packages=find_packages(),            # Automatically find packages
    python_requires=">=3.10",
    author="komoriiwakura",
    author_email="k0mori@proton.me",                     # optional, can leave blank
    description="A Python module for parsing and rendering PawML",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/komoriiwakura/pawser",  # replace with your repo URL
    license="All rights reserved; educational/personal use only",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
    ],
)
