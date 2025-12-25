# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
from __future__ import annotations

from typing import TYPE_CHECKING
from sphinx.domains.python import PythonDomain

from sphinx.ext import intersphinx

if TYPE_CHECKING:
    from sphinx import addnodes, application, environment
    from docutils.nodes import Element
    from sphinx.application import Sphinx
    from sphinx.builders import Builder
    from sphinx.environment import BuildEnvironment
# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "MaMMoS"
copyright = "2025, Thomas Schrefl, Swapneel Amit Pathak, Andrea Petrocchi, Samuel Holt, Martin Lang, Hans Fangohr"
author = "Thomas Schrefl, Swapneel Amit Pathak, Andrea Petrocchi, Samuel Holt, Martin Lang, Hans Fangohr"
# release = '0.1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

nitpicky = True
nitpick_ignore = [
    ('py:class', 'owlready2.entity.ThingClass'),
]

extensions = [
    "myst_nb",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

myst_enable_extensions = [
    "colon_fence",
]
templates_path = ["_templates"]
autosummary_generate = True
autosummary_generate_overwrite = True
autodoc_mock_imports = ["esys-escript"]
autoclass_content = "both"
autodoc_typehints = "description"
autodoc_default_options = {
    # Autodoc members
    "members": True,
    # Autodoc undocumented memebers
    "undoc-members": True,
    # Autodoc private memebers
    "private-members": False,
    # Autodoc special members (for the moment only __init__)
    # "special-members": "__init__",
    "special-members": "__class_getitem__",
}
intersphinx_mapping = {
    "astropy": ("https://docs.astropy.org/en/stable", None),
    "ontopy": ("https://emmo-repo.github.io/EMMOntoPy/latest/", None),
    "matplotlib": ("https://matplotlib.org/stable", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "owlready2": ("https://owlready2.readthedocs.io/en/latest/", None),
    "pandas": ("https://pandas.pydata.org/docs/", None),
    "pydantic": ("https://docs.pydantic.dev/latest", None),
    "python": ("https://docs.python.org/3", None),
    "pyvista": ("https://docs.pyvista.org/", None),
}
exclude_patterns = ["**.ipynb_checkpoints"]
numfig = True
numfig_format = {
    'figure': 'Figure %s',
    'table': 'Table %s',
    'code-block': 'Listing %s',
}
nb_execution_mode = "off"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "pydata_sphinx_theme"
html_static_path = ["_static"]
html_css_files = ["css/custom.css"]
html_logo = "_static/logo.png"
html_favicon = "_static/favicon.png"
html_show_sourcelink = False
html_sourcelink_suffix = ''
html_theme_options = {
    "external_links": [
        {"name": "MaMMoS project", "url": "https://mammos-project.github.io"},
    ],
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/MaMMoS-project",
            "icon": "fab fa-github-square",
        },
    ],
    "header_links_before_dropdown": 6,
    "logo": {
        "text": "documentation",
    },
    "secondary_sidebar_items": ["page-toc", "notebook-badges"],
}
html_sidebars = {
    "changelog": [],
    "design": [],
}


# -- Code to fix various Sphinx issues related to type hints -----------------

# code snippet for fixing mapping for pathlib.Path, taken from
# https://github.com/tox-dev/pyproject-api/blob/136e5ded8f65fb157c2e5fee5e8e05de9eefcdd4/docs/conf.py
class PatchedPythonDomain(PythonDomain):
    def resolve_xref(  # noqa: PLR0913,PLR0917
        self,
        env: BuildEnvironment,
        fromdocname: str,
        builder: Builder,
        type: str,  # noqa: A002
        target: str,
        node: resolve_xref,
        contnode: Element,
    ) -> Element:
        # fixup some wrongly resolved mappings
        mapping = {
            "pathlib._local.Path": "pathlib.Path",
        }
        if target in mapping:
            target = node["reftarget"] = mapping[target]
        return super().resolve_xref(
            env, fromdocname, builder, type, target, node, contnode
        )


# A custom handler for :py:data:`numpy.typing.ArrayLike`
# Based on https://github.com/sphinx-doc/sphinx/issues/13308
def missing_reference_handler(
    app: application.Sphinx,
    env: environment.BuildEnvironment,
    node: addnodes.pending_xref,
    contnode,
):
    target = node["reftarget"]
    if "." in target and node["reftype"] == "class":
        # Try again as `obj` so we pick up Unions, TypeVars and other things
        if target.startswith("ophyd_async"):
            # Pick it up from our domain
            domain = env.domains[node["refdomain"]]
            refdoc = node.get("refdoc")
            return domain.resolve_xref(
                env, refdoc, app.builder, "data", target, node, contnode
            )
        else:
            # pass it to intersphinx with the right type
            node["reftype"] = "data"
            return intersphinx.missing_reference(app, env, node, contnode)


def setup(app: application.Sphinx):
    app.connect("missing-reference", missing_reference_handler)
    app.add_domain(PatchedPythonDomain, override=True)
