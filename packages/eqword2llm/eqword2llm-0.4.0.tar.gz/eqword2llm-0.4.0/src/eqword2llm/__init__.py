"""
eqword2llm: Convert equation-heavy Word documents (.docx) to Markdown for LLM.

Outputs math equations in LaTeX format for accurate LLM recognition.

Example:
    >>> from eqword2llm import WordToMarkdownConverter
    >>> converter = WordToMarkdownConverter("document.docx")
    >>> markdown = converter.convert()
    >>> print(markdown)

    # Structured output with metadata
    >>> result = converter.convert_structured()
    >>> print(result.metadata.equation_count)

    # LLM-ready prompt
    >>> prompt = converter.to_llm_prompt()
"""

from eqword2llm.converter import (
    ConversionResult,
    DocumentMetadata,
    EquationInfo,
    WordToMarkdownConverter,
)

__version__ = "0.4.0"
__all__ = [
    "WordToMarkdownConverter",
    "ConversionResult",
    "DocumentMetadata",
    "EquationInfo",
    "__version__",
]
