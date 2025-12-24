# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options.
# For a full list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup -------------------------------------------------------

# If extensions (or modules to document with autodoc) are in
# another directory, add these directories to sys.path here. If the
# directory is relative to the documentation root, use os.path.abspath
# to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('..'))


# -- Project information ----------------------------------------------

project = 'kep_solver'
copyright = '2024, William Pettersson'
author = 'William Pettersson'


# -- General configuration --------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ['sphinx.ext.autodoc',
              'sphinx.ext.autosummary',
              'sphinx_autodoc_typehints',
              'sphinx.ext.napoleon',
              'myst_parser',
              ]

# Add any paths that contain templates here, relative to this directory
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

source_suffix = [".rst", ".md"]

autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__'
}

def run_apidoc(_):
    from sphinx.ext.apidoc import main
    import os
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    cur_dir = os.path.abspath(os.path.dirname(__file__))
    module = os.path.join(cur_dir, "..", "kep_solver")
    source = os.path.join(cur_dir, "source")
    main(['-e', '-o', source, module, '--force'])


def setup(app):
    app.connect('builder-inited', run_apidoc)


# -- Options for HTML output ------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation
# for a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets)
# here, relative to this directory. They are copied after the builtin
# static files, so a file named "default.css" will overwrite the
# builtin "default.css".
html_static_path = ['_static']


# A boolean that decides whether module names are prepended to all
# object names (for object types where a “module” of some kind is
# defined), e.g. for py:function directives. Default is True.
add_module_names = False
