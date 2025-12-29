# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'PAB CLI'
copyright = '2025, PAB CLI Team'
author = 'PAB CLI Team'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'myst_parser',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# Disable linkcheck builder that's causing the requests import error
linkcheck_ignore = [r'.*']

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = []  # Empty to avoid missing _static directory errors

# -- Source file parsers -----------------------------------------------------
source_suffix = {
    '.rst': None,
    '.md': 'markdown',
}

# -- MyST Parser settings ----------------------------------------------------
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "html_admonition",
    "replacements",
    "smartquotes",
    "substitution",
    "tasklist",
]
