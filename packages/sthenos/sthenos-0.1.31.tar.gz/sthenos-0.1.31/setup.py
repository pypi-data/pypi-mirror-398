from setuptools import setup, find_packages

from pathlib import Path

this_directory = Path(__file__).parent

# Automatically sync README from root if available
root_readme = this_directory.parent / "README.md"
local_readme = this_directory / "README.md"

if root_readme.exists():
    local_readme.write_text(root_readme.read_text())

long_description = local_readme.read_text()

import re

# Parse version from pyproject.toml to avoid duplication
pyproject_path = this_directory / "pyproject.toml"
version = "0.0.0" # Fallback
if pyproject_path.exists():
    content = pyproject_path.read_text()
    # Look for version = "x.y.z" in [project] section
    match = re.search(r'version\s*=\s*"(.*?)"', content)
    if match:
        version = match.group(1)

setup(
    name="sthenos",
    version=version,
    description="A powerful, Python-scriptable load testing tool inspired by K6.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'sthenos': ['bin/*'],
    },
)
