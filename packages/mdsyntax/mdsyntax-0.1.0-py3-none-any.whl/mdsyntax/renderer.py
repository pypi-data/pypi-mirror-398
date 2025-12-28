"""
Terminal markdown renderer with syntax highlighting.
"""

from __future__ import annotations

import os
import re
import shutil
from collections.abc import Iterator
from dataclasses import dataclass, field

from colorama import Back, Fore, Style, init
from pygments import highlight
from pygments.formatters import Terminal256Formatter, TerminalTrueColorFormatter
from pygments.lexers import TextLexer, get_lexer_by_name, guess_lexer
from pygments.styles import get_all_styles, get_style_by_name

init(autoreset=True)


class Ansi:
    """ANSI escape codes not exposed by colorama."""

    ITALIC = "\033[3m"
    ITALIC_OFF = "\033[23m"
    UNDERLINE = "\033[4m"
    UNDERLINE_OFF = "\033[24m"
    DIM = "\033[2m"
    DIM_OFF = "\033[22m"
    STRIKETHROUGH = "\033[9m"
    STRIKETHROUGH_OFF = "\033[29m"


LANG_ALIASES: dict[str, str] = {
    "py": "python",
    "js": "javascript",
    "ts": "typescript",
    "sh": "bash",
    "shell": "bash",
    "yml": "yaml",
    "md": "markdown",
    "c++": "cpp",
    "c#": "csharp",
}


def _detect_true_color() -> bool:
    """Check if terminal supports 24-bit color."""
    colorterm = os.environ.get("COLORTERM", "")
    return colorterm in ("truecolor", "24bit")


def _get_style_bg(style_name: str) -> str:
    """Extract background color from pygments style as ANSI escape."""
    try:
        style = get_style_by_name(style_name)
        bg = style.background_color
        if bg and bg.startswith("#") and len(bg) == 7:
            r, g, b = int(bg[1:3], 16), int(bg[3:5], 16), int(bg[5:7], 16)
            return f"\033[48;2;{r};{g};{b}m"
    except Exception:
        pass
    return "\033[48;5;236m"  # fallback gray


def _visible_len(s: str) -> int:
    """Length of string excluding ANSI escape sequences."""
    return len(re.sub(r"\033\[[0-9;]*m", "", s))


def _pad_to_width(text: str, width: int) -> str:
    """Pad string to width, accounting for ANSI codes."""
    padding = width - _visible_len(text)
    return text + " " * max(0, padding)


class SyntaxHighlighter:
    """Syntax highlighter using pygments."""

    def __init__(self, style: str = "monokai", true_color: bool | None = None):
        """
        Args:
            style: Pygments style name (monokai, dracula, gruvbox-dark, one-dark, etc.)
            true_color: Use 24-bit color. None = auto-detect from COLORTERM env var.
        """
        if true_color is None:
            true_color = _detect_true_color()

        formatter_cls = (
            TerminalTrueColorFormatter if true_color else Terminal256Formatter
        )
        self.formatter = formatter_cls(style=style)
        self.style = style

    def highlight(self, code: str, language: str = "") -> str:
        """Highlight code and return ANSI-formatted string."""
        lexer = self._get_lexer(code, language)
        return highlight(code, lexer, self.formatter).rstrip("\n")

    def _get_lexer(self, code: str, language: str):
        language = LANG_ALIASES.get(language.lower(), language.lower())

        if language:
            try:
                return get_lexer_by_name(language)
            except Exception:
                pass

        try:
            return guess_lexer(code)
        except Exception:
            return TextLexer()

    @staticmethod
    def available_styles() -> list[str]:
        """Return list of available pygments style names."""
        return list(get_all_styles())


@dataclass
class MarkdownRenderer:
    """Renders markdown to ANSI-formatted terminal output."""

    code_style: str = "monokai"
    code_width: int | None = None  # None = terminal width
    true_color: bool | None = None  # None = auto-detect

    _highlighter: SyntaxHighlighter = field(init=False, repr=False)
    _code_bg: str = field(init=False, repr=False)

    def __post_init__(self):
        self._highlighter = SyntaxHighlighter(
            style=self.code_style, true_color=self.true_color
        )
        self._code_bg = _get_style_bg(self.code_style)

    def render(self, text: str) -> str:
        """Render markdown text to ANSI-formatted string."""
        # Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        return "\n".join(self._render_blocks(text))

    def _render_blocks(self, text: str) -> Iterator[str]:
        """Process block-level elements."""
        lines = text.split("\n")
        i = 0

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Code block
            if stripped.startswith("```"):
                lang = stripped[3:].strip()
                code_lines = []
                i += 1

                while i < len(lines) and not lines[i].strip().startswith("```"):
                    code_lines.append(lines[i])
                    i += 1

                yield from self._render_code_block(code_lines, lang)
                i += 1  # skip closing ```
                continue

            yield self._render_line(line)
            i += 1

    def _get_code_width(self) -> int:
        if self.code_width:
            return self.code_width
        return shutil.get_terminal_size().columns

    def _render_code_block(self, code_lines: list[str], language: str) -> Iterator[str]:
        """Render a fenced code block with syntax highlighting."""
        width = self._get_code_width()
        bg = self._code_bg
        reset = Style.RESET_ALL

        # Header with language label
        label = f"{language}" if language else ""
        if label:
            yield f"{bg}{Fore.LIGHTBLACK_EX}{_pad_to_width(label, width)}{reset}"

        # Highlighted code
        if code_lines:
            code = "\n".join(code_lines)
            highlighted = self._highlighter.highlight(code, language)

            for hl_line in highlighted.split("\n"):
                yield f"{bg}{_pad_to_width(hl_line, width)}{reset}"

    def _render_line(self, line: str) -> str:
        """Render a single line of markdown."""
        stripped = line.strip()

        if not stripped:
            return ""

        # Horizontal rule
        if re.match(r"^[-*_]{3,}$", stripped):
            return f"{Ansi.DIM}{Fore.WHITE}{'─' * 50}{Style.RESET_ALL}"

        # Headers
        if m := re.match(r"^(#{1,6})\s+(.+)$", stripped):
            return self._render_header(len(m.group(1)), m.group(2))

        # Blockquotes
        if stripped.startswith(">"):
            content = stripped.lstrip(">").strip()
            rendered = self._render_inline(content)
            return f"{Fore.MAGENTA}│ {Ansi.ITALIC}{rendered}{Ansi.ITALIC_OFF}{Style.RESET_ALL}"

        # Task lists
        if m := re.match(r"^[-*]\s+\[([ xX])\]\s+(.+)$", stripped):
            checked = m.group(1).lower() == "x"
            marker = f"{Fore.GREEN}✓" if checked else f"{Fore.RED}○"
            return f"  {marker} {self._render_inline(m.group(2))}{Style.RESET_ALL}"

        # Unordered lists
        if m := re.match(r"^[-*+]\s+(.+)$", stripped):
            indent = len(line) - len(line.lstrip())
            return f"{' ' * indent}{Fore.GREEN}• {Style.RESET_ALL}{self._render_inline(m.group(1))}"

        # Ordered lists
        if m := re.match(r"^(\d+)\.\s+(.+)$", stripped):
            indent = len(line) - len(line.lstrip())
            return f"{' ' * indent}{Fore.GREEN}{m.group(1)}. {Style.RESET_ALL}{self._render_inline(m.group(2))}"

        return self._render_inline(line)

    def _render_header(self, level: int, text: str) -> str:
        """Render a header with level-appropriate styling."""
        colors = [
            Fore.CYAN,
            Fore.BLUE,
            Fore.MAGENTA,
            Fore.GREEN,
            Fore.YELLOW,
            Fore.WHITE,
        ]
        color = colors[min(level, 6) - 1]

        # Visual prefix for h1-h3
        prefix = "█" * (4 - level) + " " if level <= 3 else ""

        rendered_text = self._render_inline(text)
        return f"{color}{Style.BRIGHT}{prefix}{rendered_text}{Style.RESET_ALL}"

    def _render_inline(self, text: str) -> str:
        """Render inline markdown elements."""
        # Order matters: process from most specific to least specific

        # Inline code first (protects contents from further processing)
        code_spans: list[str] = []

        def extract_code(m):
            code_spans.append(
                f"{Back.BLACK}{Fore.YELLOW} {m.group(1)} {Style.RESET_ALL}"
            )
            return f"\x00CODE{len(code_spans) - 1}\x00"

        text = re.sub(r"`([^`]+)`", extract_code, text)

        # Bold + italic (must come before bold and italic)
        text = re.sub(
            r"\*\*\*(.+?)\*\*\*",
            lambda m: f"{Style.BRIGHT}{Ansi.ITALIC}{m.group(1)}{Ansi.ITALIC_OFF}{Style.NORMAL}",
            text,
        )

        # Bold
        text = re.sub(
            r"\*\*(.+?)\*\*",
            lambda m: f"{Style.BRIGHT}{m.group(1)}{Style.NORMAL}",
            text,
        )
        text = re.sub(
            r"__(.+?)__",
            lambda m: f"{Style.BRIGHT}{m.group(1)}{Style.NORMAL}",
            text,
        )

        # Italic with asterisks (works anywhere)
        text = re.sub(
            r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)",
            lambda m: f"{Ansi.ITALIC}{m.group(1)}{Ansi.ITALIC_OFF}",
            text,
        )

        # Italic with underscores (only at word boundaries)
        text = re.sub(
            r"(?<!\w)_(?!_)(.+?)(?<!_)_(?!\w)",
            lambda m: f"{Ansi.ITALIC}{m.group(1)}{Ansi.ITALIC_OFF}",
            text,
        )

        # Strikethrough
        text = re.sub(
            r"~~(.+?)~~",
            lambda m: f"{Ansi.STRIKETHROUGH}{m.group(1)}{Ansi.STRIKETHROUGH_OFF}",
            text,
        )

        # Links
        text = re.sub(
            r"\[([^\]]+)\]\(([^)]+)\)",
            lambda m: f"{Ansi.UNDERLINE}{Fore.BLUE}{m.group(1)}{Ansi.UNDERLINE_OFF}{Style.RESET_ALL}{Ansi.DIM} ({m.group(2)}){Ansi.DIM_OFF}",
            text,
        )

        # Restore code spans
        for i, code in enumerate(code_spans):
            text = text.replace(f"\x00CODE{i}\x00", code)

        return text


def md_print(
    text: str,
    *,
    code_style: str = "monokai",
    code_width: int | None = None,
    true_color: bool | None = None,
) -> None:
    """
    Print markdown-formatted text to the terminal.

    Args:
        text: Markdown text to render.
        code_style: Pygments style for code blocks.
        code_width: Width for code blocks (None = terminal width).
        true_color: Use 24-bit color (None = auto-detect).
    """
    renderer = MarkdownRenderer(
        code_style=code_style,
        code_width=code_width,
        true_color=true_color,
    )
    print(renderer.render(text))


def md_render(
    text: str,
    *,
    code_style: str = "monokai",
    code_width: int | None = None,
    true_color: bool | None = None,
) -> str:
    """
    Render markdown text to ANSI-formatted string.

    Args:
        text: Markdown text to render.
        code_style: Pygments style for code blocks.
        code_width: Width for code blocks (None = terminal width).
        true_color: Use 24-bit color (None = auto-detect).

    Returns:
        ANSI-formatted string ready for terminal output.
    """
    renderer = MarkdownRenderer(
        code_style=code_style,
        code_width=code_width,
        true_color=true_color,
    )
    return renderer.render(text)
