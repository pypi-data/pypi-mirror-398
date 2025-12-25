# Configuration file for the Sphinx documentation builder.
from __future__ import annotations
import os
import sys
from datetime import datetime


# -- Path setup --------------------------------------------------------------
# Add the project root so autodoc can import assistant_stream_ce
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# -- Project information -----------------------------------------------------
project = "assistant-stream-ce"
author = "Contributors"
copyright = f"{datetime.utcnow().year}, {author}"

# Try to read version from the package if present
try:
    
    print("trying to import - ")
    import assistant_stream_ce  # noqa: F401
    print("imported assistant-stream-ce")
    release = getattr(assistant_stream_ce, "__version__", "0.0.0")
except Exception:
    release = "0.0.0"

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.extlinks",
]

autosummary_generate = True
autodoc_typehints = "description"
autodoc_member_order = "bysource"
napoleon_google_docstring = True
napoleon_numpy_docstring = False

templates_path = ["_templates"]
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
html_theme = "furo"
html_title = project
html_static_path = ["_static"]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "starlette": ("https://www.starlette.io/", None),
    "fastapi": ("https://fastapi.tiangolo.com/", None),
}

#extlinks = {
#    "sse": ("https://html.spec.whatwg.org/multipage/server-sent-events.html#server-sent-events", "SSE"),
#}
