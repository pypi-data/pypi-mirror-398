# Configuration file for the Sphinx documentation builder.
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/config.html

import os
import sys
from pathlib import Path

# Add the source directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# -- Project information -------------------------------------------------------
project = 'BLE2WLED'
copyright = '2025, BLE2WLED Contributors'
author = 'Tobias Hildebrand'
release = '1.0.0'

# -- General configuration -----------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx.ext.viewcode',
    'sphinx_rtd_theme',
    'myst_parser',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# Create _static directory if it doesn't exist
static_path = Path(__file__).parent / '_static'
static_path.mkdir(exist_ok=True)

# -- Options for HTML output --------------------------------------------------
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_logo = None
html_favicon = None

html_theme_options = {
    'prev_next_buttons_location': 'bottom',
    'style_external_links': False,
    'vcs_pageview_mode': '',
    'style_nav_header_background': '#2980B9',
}

# -- Options for autodoc output -----------------------------------------------
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'show-inheritance': True,
}

autosummary_generate = True

# Suppress expected warnings that don't affect documentation quality
suppress_warnings = [
    'autodoc.duplicate_object_description',  # From autodoc generating both explicit and auto docs
    'toctree.toc-duplicated',  # From modules in both api/modules and index
]

# -- Options for Napoleon extension -------------------------------------------
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_keyword = True
napoleon_use_param = True
napoleon_use_rtype = True

# -- Options for MyST parser -------------------------------------------------
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "dollarmath",
    "html_image",
]

# -- Options for Intersphinx -------------------------------------------------
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'requests': ('https://requests.readthedocs.io/en/latest/', None),
}
