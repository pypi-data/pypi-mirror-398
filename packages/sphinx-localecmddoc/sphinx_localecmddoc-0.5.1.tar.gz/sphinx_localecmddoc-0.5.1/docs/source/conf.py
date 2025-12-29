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
copyright = '© jbox 2025-%Y, CC-BY-SA 4.0'
author = 'jbox'
release = data['project']['version']
version = '.'.join(release.split('.')[:2])
needs_sphinx = '8.1'
add_module_names = False

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'autodoc2',
    'myst_parser',
    'sphinx.ext.intersphinx',
    'localecmddoc',
]

# Extension Settings: autodoc2
autodoc2_packages = [
    "../../src/localecmddoc",
]
autodoc2_index_template = None
autodoc2_hidden_objects = ['undoc', 'dunder', 'private', 'inherited']

# To use myst in docstrings
autodoc2_render_plugin = "myst"

# Extension Settings: myst-parser
myst_enable_extensions = [
    "fieldlist",
    "colon_fence",
    "attrs_block",
    "deflist",
    "tasklist",
]
myst_heading_anchors = 3
language = 'en'

templates_path = ['_templates']

source_suffix = {'.md': 'markdown'}
# Extension Settings: intersphinx
intersphinx_mapping = {'python': ('https://docs.python.org/3', None)}

# extension settings: localecmddoc
localecmd_modules = {
    'localecmd.builtins': 'localecmd-builtins',
}
localecmd_codeblocks_language = ''

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_nefertiti'
html_static_path = []  # type: ignore[var-annotated]

html_theme_options = {
    # ... Other options here ...
    "repository_url": "https://codeberg.org/jbox/sphinx-localecmddoc/",
    "repository_name": "sphinx-localecmddoc",
}
