# Configuration file for the Sphinx documentation builder.

import os
import sys

sys.path.insert(0, os.path.abspath("../../"))

# -- Project information -----------------------------------------------------

author = "Titouan Le Gourrierec"
copyright = "2025, Titouan Le Gourrierec"
project = "elevatr"


def get_version():
    """Get the version number."""
    with open("../../elevatr/_version.py") as f:
        for line in f:
            if line.startswith("__version__"):
                return line.split("=")[-1].strip().strip("'").strip('"')


# The full version, including alpha/beta/rc tags
version = release = get_version()


# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
]

templates_path = ["_templates"]
exclude_patterns: list[str] = []


# -- Options for HTML output -------------------------------------------------

html_theme = "furo"
html_favicon = "_static/favicon.ico"
html_static_path = ["_static"]
html_show_sourcelink = False

# -- Options for autodoc -------------------------------------------------

autodoc_typehints = "description"
autodoc_member_order = "bysource"
autodoc_inherit_docstrings = False

# -- Options for napoleon -------------------------------------------------

napoleon_numpy_docstring = True
