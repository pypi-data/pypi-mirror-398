# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'phrugal'
copyright = '2024, Martin Demling'
author = 'Martin Demling'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx_rtd_theme",
    "sphinx.ext.autosectionlabel"
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# The short X.Y version.
import phrugal
version = phrugal.__version__
# The full version, including alpha/beta/rc tags.
release = version



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

html_context = {
    "display_github": True, # Integrate GitHub
    "github_user": "0x6d64", # Username
    "github_repo": "phrugal", # Repo name
    "github_version": "master", # Version
    "conf_py_path": "/doc/", # Path in the checkout to the docs root
}
html_logo = "./img/phrugal-logo-draft-small.png"