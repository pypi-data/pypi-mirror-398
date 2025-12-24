# eqword2llm

[![PyPI version](https://img.shields.io/pypi/v/eqword2llm.svg)](https://pypi.org/project/eqword2llm/)
[![PyPI downloads](https://img.shields.io/pypi/dm/eqword2llm.svg)](https://pypi.org/project/eqword2llm/)
[![Python](https://img.shields.io/pypi/pyversions/eqword2llm.svg)](https://pypi.org/project/eqword2llm/)
[![CI](https://github.com/manabelab/eqword2llm/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/manabelab/eqword2llm/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Equation Word → LLM**: Convert equation-heavy Word documents (.docx) to Markdown with LaTeX math for LLM recognition.

## Why eqword2llm?

Most Word-to-Markdown converters **ignore or break mathematical equations**. `eqword2llm` is specifically designed for **scientific and technical documents** where math equations are critical.

<p align="center">
  <img src="docs/conversion-flow.svg" alt="Word to Markdown conversion flow" width="700">
</p>

## Features

- 🔢 **Math equation conversion** - OMML to LaTeX (inline `$...$` and block `$$...$$`)
- 🔖 **Automatic equation numbering** - Block equations get `\tag{N}` (can be disabled)
- 🤖 **LLM-optimized output** - Clean Markdown that LLMs can understand
- 🌍 **Full Unicode support** - Japanese, Chinese, Korean, and more
- 📊 Tables, lists, headings, formatting support
- 🐍 **Zero dependencies** - Python standard library only

## Installation

```bash
# PyPI
pip install eqword2llm

# or with uv
uv add eqword2llm
```

## Quick Start

### Command Line

```bash
# Output to stdout (with equation numbers by default)
eqword2llm document.docx

# Output to file
eqword2llm document.docx -o output.md

# Disable equation numbering
eqword2llm document.docx -o output.md --no-equation-numbers
```

### Python API

```python
from eqword2llm import WordToMarkdownConverter

# With equation numbers (default)
converter = WordToMarkdownConverter("research_paper.docx")
markdown = converter.convert()

# Without equation numbers
converter = WordToMarkdownConverter("research_paper.docx", equation_numbers=False)
markdown = converter.convert()
```

### With LLM APIs

```python
import anthropic
from eqword2llm import WordToMarkdownConverter

# Convert Word document with equations
converter = WordToMarkdownConverter("math_paper.docx")
markdown = converter.convert()

# Send to Claude - equations are now readable!
client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": f"Explain the equations in this document:\n\n{markdown}"}
    ]
)
```

## Equation Numbering

Block equations are automatically numbered using LaTeX `\tag{N}` syntax:

**With numbering (default):**

```latex
$$
E = mc^{2} \tag{1}
$$

$$
F = ma \tag{2}
$$
```

**Without numbering (`equation_numbers=False` or `--no-equation-numbers`):**

```latex
$$
E = mc^{2}
$$

$$
F = ma
$$
```

## Supported Math Elements

| Element | LaTeX Output |
|---------|-------------|
| Fraction | `\frac{a}{b}` |
| Superscript | `x^{2}` |
| Subscript | `x_{i}` |
| Radical | `\sqrt{x}`, `\sqrt[n]{x}` |
| Integral | `\int_{a}^{b} f(x) dx` |
| Summation | `\sum_{i=1}^{n} x_i` |
| Matrix | `\begin{pmatrix}...\end{pmatrix}` |
| Greek letters | `\alpha`, `\beta`, `\gamma` ... |
| Functions | `\sin`, `\cos`, `\log`, `\lim` ... |
| Brackets | `\left(...\right)` |
| Accents | `\hat{x}`, `\vec{v}`, `\bar{x}` |

## Multilingual Support

Full support for documents in any language:

| Language | Support |
|----------|---------|
| Japanese (日本語) | ✅ Hiragana, Katakana, Kanji |
| Chinese (中文) | ✅ Simplified and Traditional |
| Korean (한국어) | ✅ Hangul |
| Arabic (العربية) | ✅ RTL text |
| Cyrillic (Русский) | ✅ Russian, Ukrainian, etc. |

Math symbols (α, β, ∑, ∫, etc.) are converted to LaTeX while preserving surrounding text.

## Development

```bash
# Clone and setup
git clone https://github.com/manabelab/eqword2llm.git
cd eqword2llm
uv sync --dev

# Run tests
uv run pytest tests/ -v

# Lint and type check
uv run ruff check src tests
uv run mypy src
```

## Comparison with Other Tools

| Feature | eqword2llm | mammoth | pandoc |
|---------|------------|---------|--------|
| Math equations | ✅ LaTeX | ❌ | △ Partial |
| Equation numbering | ✅ | ❌ | △ |
| Zero dependencies | ✅ | ❌ | ❌ |
| LLM-optimized | ✅ | ❌ | ❌ |
| Unicode support | ✅ | ✅ | ✅ |

## Limitations

- Images are not currently supported
- Complex layouts (multiple columns, text boxes) are simplified
- Some special math symbols may not be converted

## License

MIT License - See [LICENSE](LICENSE) for details.

## Contributing

Issues and Pull Requests are welcome!
