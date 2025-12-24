# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

from importlib.metadata import version as get_version

project = "WuttaSync"
copyright = "2024, Lance Edgar"
author = "Lance Edgar"
release = get_version("WuttaSync")

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx.ext.todo",
    "enum_tools.autoenum",
    "sphinxcontrib.programoutput",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "rattail-manual": ("https://docs.wuttaproject.org/rattail-manual/", None),
    "sqlalchemy": ("http://docs.sqlalchemy.org/en/latest/", None),
    "sqlalchemy-continuum": (
        "https://sqlalchemy-continuum.readthedocs.io/en/latest/",
        None,
    ),
    "sqlalchemy-utils": ("https://sqlalchemy-utils.readthedocs.io/en/latest/", None),
    "wutta-continuum": ("https://docs.wuttaproject.org/wutta-continuum/", None),
    "wuttjamaican": ("https://docs.wuttaproject.org/wuttjamaican/", None),
}


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]
