from setuptools import setup, find_packages
from pathlib import Path

# Read README.md content
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="physics_x_optics_cbse",
    version="1.0.2",
    packages=find_packages(),
    description="Class 10 CBSE Optics Helper Library",
    author="Dinesh_Pandiyan_B",
    author_email="rajadineshp@gmail.com",
    long_description=long_description,
    long_description_content_type="text/markdown",

    url="https://github.com/dineshlabx/physics_x_optics_cbse",

    project_urls={
        "source code": "https://github.com/dineshlabx/physics_x_optics_cbse",

        "Bug Tracker": "https://github.com/dineshlabx/physics_x_optics_cbse",
    },

)
