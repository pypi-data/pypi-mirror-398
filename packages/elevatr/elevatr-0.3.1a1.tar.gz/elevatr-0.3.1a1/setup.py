import pathlib

from setuptools import find_packages, setup

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()


def get_version():
    """Get the version number."""
    with open("elevatr/_version.py") as f:
        for line in f:
            if line.startswith("__version__"):
                return line.split("=")[-1].strip().strip("'").strip('"')


setup(
    name="elevatr",
    version=get_version(),
    author="Titouan Le Gourrierec",
    author_email="titouanlegourrierec@icloud.com",
    description="A Python package to simplify downloading and processing elevation data.",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/titouanlegourrierec/elevatr",
    project_urls={
        "Documentation": "https://elevatr.readthedocs.io",
        "Bug Tracker": "https://github.com/titouanlegourrierec/elevatr/issues",
    },
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: GIS",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=[
        "contextily",
        "geopandas",
        "matplotlib",
        "numpy",
        "pandas",
        "pyproj",
        "pyvista",
        "rasterio",
        "requests",
        "rioxarray",
        "shapely",
        "tqdm",
    ],
    extras_require={
        "dev": [
            "black",
            "codecov",
            "coverage",
            "flake8",
            "mypy",
            "pre-commit",
            "pytest",
            "pytest-xdist",
            "sphinx",
            "sphinx-autodoc-typehints",
            "furo",
        ],
    },
)
