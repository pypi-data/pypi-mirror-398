# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys

sys.path.insert(0, os.path.abspath('..'))

project = 'APCloudy'
copyright = '2025, Fawad Ali'
author = 'Fawad Ali'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx.ext.autosummary',
    'myst_parser',
    'sphinx_copybutton',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# RTD Theme specific options
html_theme_options = {
    'analytics_id': '',
    'analytics_anonymize_ip': False,
    'logo_only': False,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': False,
    'vcs_pageview_mode': '',
    'style_nav_header_background': '#2c3e50',  # Dark blue header
    # Sidebar options
    'collapse_navigation': False,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False,
}

# Add custom CSS files - this ensures they're loaded after the theme CSS
html_css_files = [
    'css/dark_theme.css',
]


# Ensure static files are copied
def setup(app):
    app.add_css_file('css/dark_theme.css')


# Custom context for RTD
html_context = {
    'display_github': True,
    'github_user': 'yourusername',  # Replace with your GitHub username
    'github_repo': 'apcloudy',  # Replace with your repo name
    'github_version': 'main/docs/',
}

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

# Autodoc settings
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}

# Intersphinx mapping
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'requests': ('https://requests.readthedocs.io/en/latest/', None),
}

# Source file extensions
source_suffix = {
    '.rst': None,
    '.md': 'myst_parser',
}

# Copy button configuration for code blocks
copybutton_prompt_text = r">>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
copybutton_prompt_is_regexp = True
copybutton_only_copy_prompt_lines = True

# Syntax highlighting - use a lighter dark theme for better compatibility
pygments_style = 'monokai'
