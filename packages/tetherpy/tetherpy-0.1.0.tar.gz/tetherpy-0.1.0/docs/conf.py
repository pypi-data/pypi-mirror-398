import os
import sys
import re
# Ensure Sphinx can find the source code
sys.path.insert(0, os.path.abspath("../src"))


def get_project_metadata():
    import pathlib
    import sys

    pyproject_path = pathlib.Path(__file__).parents[1] / "pyproject.toml"
    if sys.version_info >= (3, 11):
        import tomllib

        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
    else:
        try:
            import tomli

            with open(pyproject_path, "rb") as f:
                data = tomli.load(f)
        except ImportError:
            return {}
    project = data.get("project", {})
    author = project.get("authors", [{}])[0].get("name", "")
    copyright_year = re.search(r"\\d{4}", project.get("version", ""))
    copyright_str = f"{copyright_year.group(0) if copyright_year else ''}, {author}"
    return {
        "project": project.get("name", "SheetWise"),
        "author": author,
        "release": project.get("version", "0.0.0"),
        "copyright": copyright_str,
    }


meta = get_project_metadata()

project = 'Tether'
copyright = '2025, Khushiyant'
author = meta.get("author", "Khushiyant")
release = meta.get("release", "0.1.0")

extensions = [
    'sphinx.ext.autodoc',      # Core library for html generation from docstrings
    'sphinx.ext.autosummary',  # Create neat summary tables
    'sphinx.ext.napoleon',     # Support for NumPy/Google style docstrings
    'sphinx.ext.viewcode',     # Add links to highlighted source code
    'myst_parser',             # Support for Markdown files
    'sphinx_autodoc_typehints' # Show type hints in docs
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_static_path = ["_static"]
html_theme = "furo"

# Optional: Furo specific customization
html_theme_options = {
    "source_repository": "https://github.com/Khushiyant/tenso",
    "source_branch": "main",
    "source_directory": "docs/source/",
}

suppress_warnings = [
    'myst.xref_missing',  # Suppress MyST cross-reference errors
]