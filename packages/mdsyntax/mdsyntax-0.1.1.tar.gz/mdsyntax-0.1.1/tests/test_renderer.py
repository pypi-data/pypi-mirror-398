"""Tests for mdsyntax."""

import re

from mdsyntax import LANG_ALIASES, MarkdownRenderer, SyntaxHighlighter, md_render


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from text."""
    return re.sub(r"\033\[[0-9;]*m", "", text)


class TestInlineFormatting:
    def test_bold_asterisks(self):
        result = md_render("**bold**")
        assert "bold" in strip_ansi(result)
        assert "**" not in strip_ansi(result)

    def test_bold_underscores(self):
        result = md_render("__bold__")
        assert "bold" in strip_ansi(result)
        assert "__" not in strip_ansi(result)

    def test_italic_asterisks(self):
        result = md_render("*italic*")
        assert "italic" in strip_ansi(result)
        assert strip_ansi(result).count("*") == 0

    def test_italic_underscores(self):
        result = md_render("_italic_")
        assert "italic" in strip_ansi(result)

    def test_underscore_in_word_preserved(self):
        result = md_render("some_variable_name")
        assert "some_variable_name" in strip_ansi(result)

    def test_multiple_italics(self):
        result = md_render("*a* and *b*")
        plain = strip_ansi(result)
        assert "a" in plain
        assert "b" in plain
        assert "*" not in plain

    def test_bold_italic(self):
        result = md_render("***both***")
        assert "both" in strip_ansi(result)

    def test_strikethrough(self):
        result = md_render("~~deleted~~")
        assert "deleted" in strip_ansi(result)
        assert "~~" not in strip_ansi(result)

    def test_inline_code(self):
        result = md_render("`code`")
        assert "code" in strip_ansi(result)

    def test_code_protects_formatting(self):
        result = md_render("`**not bold**`")
        assert "**not bold**" in strip_ansi(result)

    def test_link(self):
        result = md_render("[text](https://example.com)")
        plain = strip_ansi(result)
        assert "text" in plain
        assert "example.com" in plain


class TestBlockFormatting:
    def test_header_h1(self):
        result = md_render("# Title")
        assert "Title" in strip_ansi(result)
        assert "#" not in strip_ansi(result)

    def test_header_h2(self):
        result = md_render("## Subtitle")
        assert "Subtitle" in strip_ansi(result)

    def test_unordered_list(self):
        result = md_render("- item")
        assert "item" in strip_ansi(result)
        assert "•" in strip_ansi(result)

    def test_ordered_list(self):
        result = md_render("1. first")
        assert "first" in strip_ansi(result)
        assert "1." in strip_ansi(result)

    def test_task_list_checked(self):
        result = md_render("- [x] done")
        plain = strip_ansi(result)
        assert "done" in plain
        assert "✓" in plain

    def test_task_list_unchecked(self):
        result = md_render("- [ ] todo")
        plain = strip_ansi(result)
        assert "todo" in plain
        assert "○" in plain

    def test_blockquote(self):
        result = md_render("> quoted")
        plain = strip_ansi(result)
        assert "quoted" in plain
        assert "│" in plain

    def test_horizontal_rule(self):
        result = md_render("---")
        assert "─" in strip_ansi(result)

    def test_code_block(self):
        result = md_render("```python\nprint('hi')\n```")
        assert "print" in strip_ansi(result)


class TestEdgeCases:
    def test_empty_string(self):
        result = md_render("")
        assert result == ""

    def test_whitespace_only(self):
        result = md_render("   ")
        assert strip_ansi(result) == ""

    def test_unclosed_bold(self):
        result = md_render("**unclosed")
        assert "**unclosed" in strip_ansi(result)

    def test_unclosed_code_block(self):
        # Should not crash
        result = md_render("```python\ncode")
        assert "code" in strip_ansi(result)

    def test_crlf_normalized(self):
        result = md_render("line1\r\nline2")
        assert "\r" not in result

    def test_nested_formatting(self):
        result = md_render("**bold with `code` inside**")
        plain = strip_ansi(result)
        assert "bold with" in plain
        assert "code" in plain


class TestSyntaxHighlighter:
    def test_highlight_python(self):
        hl = SyntaxHighlighter()
        result = hl.highlight("def foo(): pass", "python")
        assert "def" in strip_ansi(result)

    def test_language_alias(self):
        hl = SyntaxHighlighter()
        result = hl.highlight("x = 1", "py")
        # Should not crash, should highlight
        assert "x" in strip_ansi(result)

    def test_available_styles(self):
        styles = SyntaxHighlighter.available_styles()
        assert "monokai" in styles
        assert len(styles) > 10


class TestMarkdownRenderer:
    def test_custom_style(self):
        renderer = MarkdownRenderer(code_style="dracula")
        result = renderer.render("# Test")
        assert "Test" in strip_ansi(result)

    def test_custom_width(self):
        renderer = MarkdownRenderer(code_width=40)
        result = renderer.render("```\ncode\n```")
        # Code block lines should be padded to 40 chars
        lines = result.split("\n")
        for line in lines:
            plain = strip_ansi(line)
            # All code block lines should be exactly 40 chars (padded)
            if plain:  # non-empty lines
                assert len(plain) == 40, f"Expected 40, got {len(plain)}: {plain!r}"


class TestLangAliases:
    def test_common_aliases(self):
        assert LANG_ALIASES["py"] == "python"
        assert LANG_ALIASES["js"] == "javascript"
        assert LANG_ALIASES["ts"] == "typescript"
        assert LANG_ALIASES["sh"] == "bash"
