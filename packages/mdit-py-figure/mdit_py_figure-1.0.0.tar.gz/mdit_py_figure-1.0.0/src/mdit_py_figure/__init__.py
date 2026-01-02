"""markdown-it-py plugin to convert image paragraphs to figure elements."""

from .index import figure_plugin

try:
    from ._version import version as __version__
except ImportError:
    __version__ = "0.0.0+unknown"  # ty: ignore[invalid-assignment]

__all__ = ("figure_plugin",)
