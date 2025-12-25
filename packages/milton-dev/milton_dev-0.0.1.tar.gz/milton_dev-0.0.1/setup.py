import setuptools
from pathlib import Path

long_desc = Path("README.md").read_text()
setuptools.setup(
    name="milton-dev",
    version="0.0.1",
    long_description=long_desc,
    packages=setuptools.find_namespace_packages(
        exclude=["mocks", "tests"]
    )
)
