import pathlib
from setuptools import find_namespace_packages, setup

from hestia_earth.models.version import VERSION

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

REQUIRES = (HERE / "requirements.txt").read_text().splitlines()

# This call to setup() does all the work
setup(
    name="hestia_earth_models",
    version=VERSION,
    description="HESTIA's set of modules for filling gaps in the activity data using external datasets (e.g. "
    "populating soil properties with a geospatial dataset using provided coordinates) and internal lookups "
    "(e.g. populating machinery use from fuel use). Includes rules for when gaps should be filled versus "
    "not (e.g. never gap fill yield, gap fill crop residue if yield provided etc.).",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://gitlab.com/hestia-earth/hestia-engine-models",
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
    extras_require={"spatial": ["hestia-earth-earth-engine>=0.6.0"]},
)
