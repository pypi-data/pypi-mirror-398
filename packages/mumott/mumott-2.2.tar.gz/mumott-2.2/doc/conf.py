#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from importlib.metadata import metadata
import sphinx_rtd_theme  # noqa: F401

sys.path.insert(0, os.path.abspath('../'))

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.mathjax',
    'sphinx.ext.ifconfig',
    'sphinx.ext.intersphinx',
    'sphinx.ext.viewcode',
    'sphinx.ext.autosummary',
    'sphinx.ext.napoleon',
    'sphinx.ext.graphviz',
    'sphinx_autodoc_typehints',
    'sphinx_sitemap',
    'nbsphinx']

graphviz_output_format = 'svg'
templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'
pygments_style = 'sphinx'
todo_include_todos = True

# Collect basic information from main module
package_metadata = metadata('mumott')
version = ''
if len(version) == 0:
    version = package_metadata['Version']
release = ''
project = package_metadata['Name']
author = package_metadata['Maintainer']

site_url = 'https://mumott.org/'
html_logo = '_static/logo.png'
html_favicon = '_static/logo.ico'
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_theme_options = {'version_selector': True}
html_context = {
    'current_version': version,
    'versions':
        [('latest release',
          '{}'.format(site_url)),
         ('development version',
          '{}/dev'.format(site_url))]}
htmlhelp_basename = 'mumottdoc'
intersphinx_mapping = \
    {'python':   ('https://docs.python.org/3', None),
     'numpy':    ('https://numpy.org/doc/stable/', None),
     'scipy':    ('https://docs.scipy.org/doc/scipy/', None),
     }

# Settings for nbsphinx
nbsphinx_execute = 'never'

# Options for LaTeX output
_PREAMBLE = r"""
\usepackage{amsmath,amssymb}
\renewcommand{\vec}[1]{\boldsymbol{#1}}
\DeclareMathOperator*{\argmin}{\arg\!\min}
\DeclareMathOperator{\argmin}{\arg\!\min}
"""

latex_elements = {
    'preamble': _PREAMBLE,
}
latex_documents = [
    (master_doc, 'mumott.tex', 'mumott Documentation',
     'The mumott developer team', 'manual'),
]


# Options for manual page output
man_pages = [
    (master_doc, 'mumott', 'mumott Documentation',
     [author], 1)
]


# Options for Texinfo output
texinfo_documents = [
    (master_doc, 'mumott', 'mumott Documentation',
     author, 'mumott', 'graph-based interatomic potentials in python',
     'Miscellaneous'),
]

html_css_files = [
    'custom.css',
]
