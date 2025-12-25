import pathlib
from setuptools import find_namespace_packages, setup

from hestia_earth.utils.version import VERSION

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

REQUIRES = (HERE / "requirements.txt").read_text().splitlines()

# This call to setup() does all the work
setup(
    name="hestia_earth_utils",
    version=VERSION,
    description="HESTIA's utils library",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://gitlab.com/hestia-earth/hestia-utils",
    author="HESTIA Team",
    author_email="guillaumeroyer.mail@gmail.com",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3.12",
    ],
    packages=find_namespace_packages(include=["hestia_earth.*"]),
    python_requires=">=3.12",
    include_package_data=True,
    install_requires=REQUIRES,
    scripts=["bin/hestia-pivot-csv", "bin/hestia-format-upload"],
)
