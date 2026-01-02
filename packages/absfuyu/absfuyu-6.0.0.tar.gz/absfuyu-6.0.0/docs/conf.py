# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

sys.path.insert(0, os.path.abspath(".."))

from absfuyu import __author__, __title__, __version__

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = f"{__title__}"
copyright = f"2022-%Y, {__author__}"
author = __author__
version = __version__
release = version

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

needs_sphinx = "8.1"

extensions = [
    "sphinx.ext.autodoc",  # include documentation
    "sphinx.ext.autosummary",
    "sphinx.ext.coverage",  # docs coverage
    "sphinx.ext.doctest",  # test docs
    "sphinx.ext.duration",
    # "sphinx.ext.extlinks", # short link
    "sphinx.ext.githubpages",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",  # This shows source code
    "sphinx_copybutton",
    "myst_parser",  # Markdown support
]

templates_path = [
    "_templates"
]

exclude_patterns = [
    "_build", "Thumbs.db", ".DS_Store"
]

language = "en"

source_suffix = {
    ".rst": "restructuredtext",
    ".txt": "markdown",
    ".md": "markdown",
}


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output


html_title = f"{__title__.upper()}'S DOCUMENTATION v{__version__}"
html_short_title = f"{__title__} v{__version__}"
# html_logo = "https://github.com/AbsoluteWinter/AbsoluteWinter.github.io/blob/75568549d30f447a66baac8ecc3b5e6b49a67d18/absfuyu/images/LOGO.png?raw=true"

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# If true, links to the reST sources are added to the pages.
html_show_sourcelink = False

# If true, "Created using Sphinx" is shown in the HTML footer. Default is True.
html_show_sphinx = False

html_sidebars = {
    "**": [
        "versioning.html",
    ],
}

# -- Extension configuration -------------------------------------------------

autodoc_member_order = "bysource"


#  -- sphinx-copybutton configuration ----------------------------------------
copybutton_prompt_text = (
    r">>> |\.\.\. |> |\$ |\# | In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
)
copybutton_prompt_is_regexp = True
copybutton_remove_prompts = True
