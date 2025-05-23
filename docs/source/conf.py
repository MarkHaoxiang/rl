# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))


# -- Project information -----------------------------------------------------
import os.path
import sys
import warnings

import pytorch_sphinx_theme
import torchrl

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning)

project = "torchrl"
copyright = "2022, Meta"
author = "Torch Contributors"

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
# version: The short X.Y version.
# release: The full version, including alpha/beta/rc tags.
if os.environ.get("RL_SANITIZE_VERSION_STR_IN_DOCS", None):
    # Turn 1.11.0aHASH into 1.11 (major.minor only)
    version = release = ".".join(torchrl.__version__.split(".")[:2])
    html_title = " ".join((project, version, "documentation"))
else:
    version = f"main ({torchrl.__version__})"
    release = "main"

os.environ["TORCHRL_CONSOLE_STREAM"] = "stdout"

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = "en"

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx.ext.mathjax",
    "sphinx.ext.napoleon",
    "sphinx_gallery.gen_gallery",
    "sphinxcontrib.aafig",
    "myst_parser",
    "sphinx_design",
]

intersphinx_mapping = {
    "torch": ("https://pytorch.org/docs/stable/", None),
    "tensordict": ("https://pytorch.github.io/tensordict/", None),
    # "torchrl": ("https://pytorch.org/rl/", None),
    "torchaudio": ("https://pytorch.org/audio/stable/", None),
    "torchtext": ("https://pytorch.org/text/stable/", None),
    "torchvision": ("https://pytorch.org/vision/stable/", None),
}


def kill_procs(gallery_conf, fname):
    import os

    import psutil

    # Get the current process
    current_proc = psutil.Process(os.getpid())
    # Iterate over all child processes
    for child in current_proc.children(recursive=True):
        # Kill the child process
        child.terminate()
        print(f"Killed child process with PID {child.pid}")  # noqa: T201


sphinx_gallery_conf = {
    "examples_dirs": "reference/generated/tutorials/",  # path to your example scripts
    "gallery_dirs": "tutorials",  # path to where to save gallery generated output
    "backreferences_dir": "gen_modules/backreferences",
    "doc_module": ("torchrl",),
    "filename_pattern": "reference/generated/tutorials/",  # files to parse
    "notebook_images": "reference/generated/tutorials/media/",  # images to parse
    "download_all_examples": True,
    "abort_on_example_error": True,
    # "show_memory": True,
    "plot_gallery": "False",
    "capture_repr": ("_repr_html_", "__repr__"),  # capture representations
    "write_computation_times": True,
    # "compress_images": ("images", "thumbnails"),
    "reset_modules": (kill_procs, "matplotlib", "seaborn"),
}

napoleon_use_ivar = True
napoleon_numpy_docstring = False
napoleon_google_docstring = True
autosectionlabel_prefix_document = True

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
source_suffix = {
    ".rst": "restructuredtext",
}

# The master toctree document.
master_doc = "index"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "pytorch_sphinx_theme"
html_theme_path = [pytorch_sphinx_theme.get_html_theme_path()]
html_theme_options = {
    "pytorch_project": "torchrl",
    "collapse_navigation": False,
    "display_version": True,
    "logo_only": False,
    "analytics_id": "UA-117752657-2",
}
html_css_files = [
    "https://cdn.jsdelivr.net/npm/katex@0.10.0-beta/dist/katex.min.css",
    "css/custom.css",
]

# Output file base name for HTML help builder.
htmlhelp_basename = "PyTorchRLdoc"

autosummary_generate = True

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# -- Options for LaTeX output ---------------------------------------------
latex_elements = {}


# -- Options for manual page output ---------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [(master_doc, "torchvision", "torchrl Documentation", [author], 1)]


# -- Options for Texinfo output -------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (
        master_doc,
        "torchrl",
        "torchrl Documentation",
        author,
        "torchrl",
        "TorchRL doc.",
        "Miscellaneous",
    ),
]


aafig_default_options = {"scale": 1.5, "aspect": 1.0, "proportional": True}

# -- Generate knowledge base references -----------------------------------
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
from content_generation import (
    generate_knowledge_base_references,
    generate_tutorial_references,
)

generate_knowledge_base_references("../../knowledge_base")
generate_tutorial_references("../../tutorials/sphinx-tutorials/", "tutorial")
# generate_tutorial_references("../../tutorials/src/", "src")
generate_tutorial_references("../../tutorials/media/", "media")

# We do this to indicate that the script is run by sphinx
import builtins

builtins.__sphinx_build__ = True
