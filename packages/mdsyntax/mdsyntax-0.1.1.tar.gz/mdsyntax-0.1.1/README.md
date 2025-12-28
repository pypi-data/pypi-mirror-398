# mdsyntax

[![PyPI version](https://img.shields.io/pypi/v/mdsyntax.svg)](https://pypi.org/project/mdsyntax/)
[![Python versions](https://img.shields.io/pypi/pyversions/mdsyntax.svg)](https://pypi.org/project/mdsyntax/)
[![CI](https://github.com/Azaias/mdsyntax/actions/workflows/ci.yml/badge.svg)](https://github.com/Azaias/mdsyntax/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Render markdown with syntax highlighting in the terminal.

## Installation

```bash
pip install mdsyntax
```

## Usage

### Python API

```python
from mdsyntax import md_print, md_render

# Print directly to terminal
md_print("""
# Hello World

This is **bold** and *italic* text.

```python
def greet(name):
    return f"Hello, {name}!"
```
""")

# Get ANSI string for further processing
output = md_render("Some `inline code` here")
```

### Command Line

```bash
# Render a file
mdsyntax README.md

# Pipe from stdin
echo "# Hello" | mdsyntax

# Use a different syntax theme
mdsyntax --style dracula document.md

# List available themes
mdsyntax --list-styles
```

## Features

- Headers (h1-h6) with color coding
- **Bold**, *italic*, ***bold italic***
- ~~Strikethrough~~
- `Inline code`
- Fenced code blocks with syntax highlighting
- [Links](https://example.com)
- Unordered and ordered lists
- Task lists
- Blockquotes
- Horizontal rules

## Configuration

### Code Styles

Any [Pygments style](https://pygments.org/styles/) is supported. Popular options:

- `monokai` (default)
- `dracula`
- `one-dark`
- `gruvbox-dark`
- `nord`
- `github-dark`

### True Color

By default, md-print auto-detects 24-bit color support via the `COLORTERM` environment variable. You can override this:

```python
# Force 256-color mode
md_print(text, true_color=False)

# Force true color
md_print(text, true_color=True)
```

## API Reference

### `md_print(text, *, code_style="monokai", code_width=None, true_color=None)`

Print markdown to terminal.

- `text`: Markdown string to render
- `code_style`: Pygments style name for code blocks
- `code_width`: Fixed width for code blocks (default: terminal width)
- `true_color`: Use 24-bit color (default: auto-detect)

### `md_render(...) -> str`

Same arguments as `md_print`, but returns the ANSI-formatted string instead of printing.

### `MarkdownRenderer`

Dataclass for more control:

```python
from mdsyntax import MarkdownRenderer

renderer = MarkdownRenderer(
    code_style="dracula",
    code_width=80,
    true_color=True,
)
output = renderer.render(markdown_text)
```

### `SyntaxHighlighter`

Standalone code highlighter:

```python
from mdsyntax import SyntaxHighlighter

hl = SyntaxHighlighter(style="monokai")
print(hl.highlight("print('hello')", "python"))
print(SyntaxHighlighter.available_styles())
```

## License

MIT


## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
