"""Command-line interface for md-print."""

from __future__ import annotations

import argparse
import sys

from mdsyntax import __version__, md_print
from mdsyntax.renderer import SyntaxHighlighter


def main(argv: list[str] | None = None) -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="mdsyntax",
        description="Render markdown with syntax highlighting in the terminal.",
    )
    parser.add_argument(
        "file",
        nargs="?",
        type=argparse.FileType("r"),
        default=sys.stdin,
        help="Markdown file to render (default: stdin)",
    )
    parser.add_argument(
        "-s",
        "--style",
        default="monokai",
        metavar="STYLE",
        help="Pygments style for code blocks (default: monokai)",
    )
    parser.add_argument(
        "-w",
        "--width",
        type=int,
        default=None,
        metavar="N",
        help="Width for code blocks (default: terminal width)",
    )
    parser.add_argument(
        "--no-true-color",
        action="store_true",
        help="Disable 24-bit true color (use 256 colors)",
    )
    parser.add_argument(
        "--list-styles",
        action="store_true",
        help="List available syntax highlighting styles and exit",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    args = parser.parse_args(argv)

    if args.list_styles:
        print("Available styles:")
        for style in sorted(SyntaxHighlighter.available_styles()):
            print(f"  {style}")
        return 0

    text = args.file.read()
    if args.file is not sys.stdin:
        args.file.close()

    true_color = None if not args.no_true_color else False

    md_print(
        text,
        code_style=args.style,
        code_width=args.width,
        true_color=true_color,
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
