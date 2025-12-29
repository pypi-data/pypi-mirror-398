"""Setup script for git-commit-ai - for backward compatibility."""

from setuptools import setup

# Read the contents of README file
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="git-commit-ai",
    long_description=long_description,
    long_description_content_type="text/markdown",
)