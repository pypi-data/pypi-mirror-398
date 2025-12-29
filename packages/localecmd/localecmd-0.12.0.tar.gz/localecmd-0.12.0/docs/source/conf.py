# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import tomllib

with open("../../pyproject.toml", "rb") as f:
    data = tomllib.load(f)

project = data['project']['name']
copyright = '© jbox 2024-%Y, CC-BY-SA 4.0'
author = 'jbox'
release = data['project']['version']
version = '.'.join(release.split('.')[:2])
needs_sphinx = '8.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'myst_parser',
    'autodoc2',
]

# Extension Settings
autodoc2_packages = [
    "../../src/localecmd",
]
autodoc2_index_template = None

# To use myst in docstrings
autodoc2_render_plugin = "myst"
# To use sphinx docstrings with myst
myst_enable_extensions = [
    "fieldlist",
    "colon_fence",
    "attrs_block",
    "deflist",
    "tasklist",
]
language = 'en'

templates_path = ['_templates']
exclude_patterns = [
    "tutorial/**",
]

source_suffix = {'.md': 'markdown'}


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_nefertiti'
html_static_path = ['_static']

html_theme_options = {
    # ... Other options here ...
    "repository_url": "https://codeberg.org/jbox/localecmd/",
    "repository_name": "localecmd",
}
