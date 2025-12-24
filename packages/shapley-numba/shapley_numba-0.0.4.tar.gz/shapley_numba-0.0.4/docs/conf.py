# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

from importlib.metadata import version as get_version

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'shapley_numba'
copyright = '2025, Shapley-numba Authors'  # noqa: A001
author = 'Shapley-numba Authors'

# Get version from package metadata (updated by tagging pipeline)
try:
    release = get_version('shapley-numba')
except Exception:
    # Fallback if package is not installed
    release = '0.0.0dev'

# Project description
html_short_title = 'shapley_numba'
html_logo = None  # Add a logo path here if you have one

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.todo',
    'sphinx.ext.napoleon',  # Support for NumPy and Google style docstrings
    'sphinx.ext.intersphinx',  # Link to other project's documentation
    'sphinx.ext.mathjax',  # Math support
    'myst_nb',
    'sphinx_rtd_dark_mode',  # Dark mode toggle
]

# Napoleon settings for better docstring parsing
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True

# Autodoc settings
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__',
}
autodoc_typehints = 'description'
autodoc_typehints_description_target = 'documented'

# Intersphinx mapping to link to other docs
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'numba': ('https://numba.readthedocs.io/en/stable/', None),
}

templates_path = ['_templates']
exclude_patterns = [
    '_build',
    'Thumbs.db',
    '.DS_Store',
    'jupyter_execute',
    '.jupyter_cache',
]

language = 'en'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_css_files = ['width-fix.css', 'dark-mode-fix.css']

# RTD theme options for better look and feel
html_theme_options = {
    'analytics_anonymize_ip': False,
    'logo_only': False,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': True,
    'collapse_navigation': False,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False,
}

# Dark mode configuration
default_dark_mode = False  # Start in light mode by default

# Additional HTML options
html_show_sourcelink = True
html_show_sphinx = True
html_show_copyright = True

# Context for the theme
html_context = {
    'display_gitlab': True,
    'gitlab_user': 'shapley-numba',
    'gitlab_repo': 'shapley-numba',
    'gitlab_version': 'master',
    'conf_py_path': '/docs/',
}

# -- Options for todo extension ----------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/todo.html#configuration

todo_include_todos = True

# myst-nb automatically registers .ipynb and .md parsers
# We can keep .rst as default
source_suffix = {
    '.rst': 'restructuredtext',
    '.ipynb': 'myst-nb',
    '.md': 'myst-nb',
}

# myst-nb configuration for better notebook rendering
nb_execution_mode = 'cache'
nb_execution_timeout = 60
nb_execution_show_tb = True
nb_output_stderr = 'show'

# Enable dollar math syntax for LaTeX in markdown cells
myst_enable_extensions = [
    'dollarmath',  # Enable $...$ and $$...$$ syntax for math
    'amsmath',  # Enable advanced math environments
]

# Ensure math is rendered properly in notebooks
myst_dmath_double_inline = True  # Render $$...$$ as display math
