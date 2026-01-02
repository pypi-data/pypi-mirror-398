"""mdit-py-heading-attris is a  markdown-it-py plugin.

It parses markdown paragraphs that start with an image into HTML `<figure>` elements.
"""

from .plugin import heading_attrs_plugin

try:
    from ._version import version as __version__
except ImportError:
    __version__ = "0.0.0+unknown"  # ty: ignore[invalid-assignment]

__all__ = ("heading_attrs_plugin",)
