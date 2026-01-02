"""
setup.py for nlpcmd-ai

This file exists for backwards compatibility.
The actual build configuration is in pyproject.toml.
"""

from setuptools import setup

# Read the contents of README file
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name="nlpcmd-ai",
    long_description=long_description,
    long_description_content_type="text/markdown",
)
