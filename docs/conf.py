# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'farmpypl'
copyright = '2026, Colm Duffy'
author = 'Colm Duffy'
release = '0.1.0'  # keep in sync with pyproject.toml

# .md and .ipynb are registered by myst_nb (which claims ".md" under its own
# parser name); .rst is built in. Do not map ".md" to "markdown" here - that
# name belongs to myst_parser, which myst_nb does not load.

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "myst_nb",
    "autoapi.extension",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.autodoc",
    "sphinx.ext.coverage",
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'html', 'Thumbs.db', '.DS_Store']

autoapi_options = [
    'members',
    'undoc-members',       # keeps modules from being skipped if docstrings are thin
    'show-inheritance',
    'show-module-summary',
    'special-members',
    'imported-members',
]

# Render example notebooks as authored (do not execute at build time) so the
# docs build is fast and deterministic. Set to "auto" to execute them.
nb_execution_mode = "off"


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

autoapi_dirs = ["../src/farmpypl"]  # location to parse for API reference
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
