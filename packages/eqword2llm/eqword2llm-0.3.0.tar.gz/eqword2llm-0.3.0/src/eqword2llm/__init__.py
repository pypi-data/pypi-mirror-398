"""
eqword2llm: Convert equation-heavy Word documents (.docx) to Markdown for LLM.

Outputs math equations in LaTeX format for accurate LLM recognition.

Example:
    >>> from eqword2llm import WordToMarkdownConverter
    >>> converter = WordToMarkdownConverter("document.docx")
    >>> markdown = converter.convert()
    >>> print(markdown)
"""

from eqword2llm.converter import WordToMarkdownConverter

__version__ = "0.3.0"
__all__ = ["WordToMarkdownConverter", "__version__"]
