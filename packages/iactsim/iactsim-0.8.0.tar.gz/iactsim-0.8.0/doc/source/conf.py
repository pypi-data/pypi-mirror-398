# Copyright (C) 2024- Davide Mollica <davide.mollica@inaf.it>
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This file is part of iactsim.
#
# iactsim is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# iactsim is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with iactsim.  If not, see <https://www.gnu.org/licenses/>.

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

# -- Path setup --------------------------------------------------------------
import pathlib
import sys
import re

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
try: # iactsim is installed
    import iactsim
except ImportError: # iactsim is run from its source checkout
    sys.path.insert(0, pathlib.Path(__file__).parents[2].resolve().as_posix())
    import iactsim

# -- Project information -----------------------------------------------------
project = 'iactsim'
copyright = '2024-, Davide Mollica'
author = 'Davide Mollica'
release = re.match(r'v?(\d+\.\d+\.\d+)', iactsim.__version__).group(1)
version = iactsim.__version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

# -- General configuration ---------------------------------------------------
# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'myst_nb',
    'IPython.sphinxext.ipython_console_highlighting',
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',  # parse numpy-style docstrings
    'sphinx.ext.autosummary',
    'sphinx_toolbox.code',  # code blocks
    'sphinx.ext.intersphinx', # links to external projects
    'autodocsumm',
    'sphinx_autodoc_typehints',
]

# Avoid calling representation methods of default values
autodoc_preserve_defaults = True

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True

templates_path = ['_templates']
exclude_patterns = []

intersphinx_mapping = {
    'numpy': ('https://numpy.org/doc/stable/', None),
    'python': ('https://docs.python.org/3/', None),
    'matplotlib': ('https://matplotlib.org/stable/', None),
    'numba': ('https://numba.readthedocs.io/en/stable/', None),
    'cupy': ('https://docs.cupy.dev/en/stable/', None),
}

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"
# html_theme = "pydata_sphinx_theme"
html_static_path = ['_static']

def setup(app):
    app.add_css_file('rtd-overrides.css')