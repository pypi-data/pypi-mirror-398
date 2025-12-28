"""
mdsyntax: Render markdown with syntax highlighting in the terminal.

Usage:
    >>> from mdsyntax import md_print, md_render
    >>> md_print("# Hello **world**")
    >>> output = md_render("Some `code` here")
"""

from mdsyntax.renderer import (
    LANG_ALIASES,
    MarkdownRenderer,
    SyntaxHighlighter,
    md_print,
    md_render,
)

__version__ = "0.1.0"
__all__ = [
    "md_print",
    "md_render",
    "MarkdownRenderer",
    "SyntaxHighlighter",
    "LANG_ALIASES",
    "__version__",
]
