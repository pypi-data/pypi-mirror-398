"""
Table converter for eqword2llm.

Contains the TableConverter class that handles conversion
of Word tables to Markdown format, including tables with equations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable
from xml.etree import ElementTree as ET

from .constants import NAMESPACES

if TYPE_CHECKING:
    pass


class TableConverter:
    """Converts Word tables to Markdown format.

    Handles tables containing equations by converting all math
    to inline format to maintain proper Markdown table structure.
    """

    def __init__(
        self,
        convert_run: Callable[[ET.Element], str],
        convert_hyperlink: Callable[[ET.Element], str],
        convert_math: Callable[[ET.Element], str],
        omml_to_latex: Callable[[ET.Element], str],
        clean_equation_number: Callable[[str], str],
    ) -> None:
        """Initialize table converter with callback functions.

        Args:
            convert_run: Function to convert text runs.
            convert_hyperlink: Function to convert hyperlinks.
            convert_math: Function to convert inline math.
            omml_to_latex: Function to convert OMML to LaTeX.
            clean_equation_number: Function to clean equation numbers.
        """
        self._convert_run = convert_run
        self._convert_hyperlink = convert_hyperlink
        self._convert_math = convert_math
        self._omml_to_latex = omml_to_latex
        self._clean_equation_number = clean_equation_number

    def convert(self, table: ET.Element) -> str:
        """Convert table to Markdown format.

        Args:
            table: XML element containing the table.

        Returns:
            Markdown formatted table string.
        """
        rows: list[list[str]] = []
        col_count = 0

        for tr in table.findall(".//w:tr", NAMESPACES):
            cells: list[str] = []
            for tc in tr.findall(".//w:tc", NAMESPACES):
                cell_content = self._get_cell_content(tc)
                cells.append(cell_content)

            if cells:
                rows.append(cells)
                col_count = max(col_count, len(cells))

        if not rows:
            return ""

        # Normalize column count (pad short rows)
        for row in rows:
            while len(row) < col_count:
                row.append("")

        # Build Markdown table
        result_lines: list[str] = []

        # Header row
        result_lines.append("| " + " | ".join(rows[0]) + " |")
        result_lines.append("| " + " | ".join(["---"] * col_count) + " |")

        # Data rows
        for row in rows[1:]:
            result_lines.append("| " + " | ".join(row) + " |")

        return "\n".join(result_lines)

    def _get_cell_content(self, cell: ET.Element) -> str:
        """Get content from a table cell.

        Converts all equations (including block equations) to inline format
        to maintain proper Markdown table structure.
        """
        parts: list[str] = []

        for para in cell.findall(".//w:p", NAMESPACES):
            para_content = self._get_cell_paragraph_content(para)
            if para_content.strip():
                parts.append(para_content.strip())

        # Join paragraphs with <br> for multi-line cells
        content = " <br> ".join(parts)

        # Escape pipe characters that would break table structure
        # but not those inside math expressions ($...$)
        content = self._escape_pipes_outside_math(content)

        return content

    def _escape_pipes_outside_math(self, text: str) -> str:
        """Escape pipe characters outside of math expressions.

        Pipe characters inside $...$ are part of LaTeX and should not be escaped.
        """
        result: list[str] = []
        in_math = False
        i = 0

        while i < len(text):
            if text[i] == "$":
                # Toggle math mode (handle $$ and $ the same way for this purpose)
                in_math = not in_math
                result.append(text[i])
            elif text[i] == "|" and not in_math:
                # Escape pipe outside math
                result.append("\\|")
            else:
                result.append(text[i])
            i += 1

        return "".join(result)

    def _get_cell_paragraph_content(self, para: ET.Element) -> str:
        """Get paragraph content for table cell.

        Similar to paragraph content extraction but converts block equations
        to inline format to work within table cells.
        """
        parts: list[str] = []

        for child in para:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag

            if tag == "r":
                run_text = self._convert_run(child)
                parts.append(run_text)
            elif tag == "hyperlink":
                hyperlink_text = self._convert_hyperlink(child)
                parts.append(hyperlink_text)
            elif tag == "oMath":
                # Inline math - convert normally
                math_text = self._convert_math(child)
                parts.append(math_text)
            elif tag == "oMathPara":
                # Block math in table cell - convert to inline format
                math_text = self._convert_math_para_inline(child)
                parts.append(math_text)

        return "".join(parts)

    def _convert_math_para_inline(self, math_para: ET.Element) -> str:
        """Convert math paragraph to inline LaTeX format.

        Used for equations within table cells where block format
        would break the table structure.
        """
        parts: list[str] = []
        for oMath in math_para.findall(".//m:oMath", NAMESPACES):
            latex = self._omml_to_latex(oMath)
            if latex:
                parts.append(latex)

        if parts:
            combined = " ".join(parts)
            # Remove Word equation numbers
            combined = self._clean_equation_number(combined)
            return f"${combined}$"
        return ""
