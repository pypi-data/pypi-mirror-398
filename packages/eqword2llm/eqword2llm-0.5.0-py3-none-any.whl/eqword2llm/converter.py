"""
eqword2llm: Equation-heavy Word document to Markdown conversion engine.

Converts OMML (Office Math Markup Language) to LaTeX format,
generating LLM-readable Markdown for scientific and technical documents.
"""

from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING
from xml.etree import ElementTree as ET

from .constants import GREEK_LETTERS, NAMESPACES
from .math_converter import OmmlToLatexConverter
from .models import ConversionResult, DocumentMetadata, EquationInfo
from .table_converter import TableConverter

if TYPE_CHECKING:
    from typing import Any

# Register namespaces for XML parsing
for prefix, uri in NAMESPACES.items():
    ET.register_namespace(prefix, uri)


class WordToMarkdownConverter:
    """Convert Word documents to Markdown."""

    def __init__(
        self,
        docx_path: str | Path,
        equation_numbers: bool = True,
    ) -> None:
        """
        Args:
            docx_path: Path to the Word document to convert.
            equation_numbers: Whether to add equation numbers to block equations.
                Defaults to True.
        """
        self.docx_path = Path(docx_path)
        self.equation_numbers = equation_numbers
        self._equation_counter = 0
        self.document_xml: ET.Element | None = None
        self.relationships: dict[str, Any] = {}
        self.numbering: dict[str, Any] = {}
        self.styles: dict[str, ET.Element] = {}

        # Metadata tracking
        self._equations: list[EquationInfo] = []
        self._heading_count = 0
        self._section_count = 0
        self._current_line = 0

        # Initialize sub-converters
        self._math_converter = OmmlToLatexConverter()
        self._table_converter: TableConverter | None = None

    def convert(self) -> str:
        """Execute conversion and return Markdown string.

        Returns:
            Converted Markdown string.

        Raises:
            FileNotFoundError: If the file is not found.
            ValueError: If the file is not a valid docx file.
        """
        # Reset metadata for fresh conversion
        self._equations = []
        self._heading_count = 0
        self._section_count = 0
        self._equation_counter = 0
        self._current_line = 0

        if not self.docx_path.exists():
            raise FileNotFoundError(f"File not found: {self.docx_path}")

        if not zipfile.is_zipfile(self.docx_path):
            raise ValueError(f"Not a valid docx file: {self.docx_path}")

        # Initialize table converter with callbacks
        self._table_converter = TableConverter(
            convert_run=self._convert_run,
            convert_hyperlink=self._convert_hyperlink,
            convert_math=self._convert_math,
            omml_to_latex=self._omml_to_latex,
            clean_equation_number=self._clean_equation_number,
        )

        with zipfile.ZipFile(self.docx_path, "r") as zf:
            # Load document.xml
            self.document_xml = ET.fromstring(zf.read("word/document.xml"))

            # Load numbering definitions if present
            if "word/numbering.xml" in zf.namelist():
                self._load_numbering(zf)

            # Load style definitions if present
            if "word/styles.xml" in zf.namelist():
                self._load_styles(zf)

        return self._convert_document()

    def convert_structured(self) -> ConversionResult:
        """Execute conversion and return structured result with metadata.

        Returns:
            ConversionResult containing markdown and metadata.
        """
        markdown = self.convert()
        metadata = DocumentMetadata(
            source=self.docx_path.name,
            equations=self._equations.copy(),
            section_count=self._section_count,
            equation_count=len(self._equations),
            heading_count=self._heading_count,
        )
        return ConversionResult(markdown=markdown, metadata=metadata)

    def to_llm_prompt(self, instructions: str | None = None) -> str:
        """Convert document and generate LLM-ready prompt.

        Args:
            instructions: Custom instructions for the LLM. If None, uses default.

        Returns:
            Complete prompt string ready to send to an LLM.
        """
        result = self.convert_structured()
        return result.to_llm_prompt(instructions)

    def _load_numbering(self, zf: zipfile.ZipFile) -> None:
        """Load numbering definitions."""
        try:
            ET.fromstring(zf.read("word/numbering.xml"))
            # Numbering processing (simplified)
        except Exception:
            pass

    def _load_styles(self, zf: zipfile.ZipFile) -> None:
        """Load style definitions."""
        try:
            styles_xml = ET.fromstring(zf.read("word/styles.xml"))
            for style in styles_xml.findall(".//w:style", NAMESPACES):
                style_id = style.get(f"{{{NAMESPACES['w']}}}styleId")
                if style_id:
                    self.styles[style_id] = style
        except Exception:
            pass

    def _convert_document(self) -> str:
        """Convert the entire document."""
        if self.document_xml is None:
            return ""

        body = self.document_xml.find(".//w:body", NAMESPACES)
        if body is None:
            return ""

        markdown_parts: list[str] = []
        list_state: dict[str, Any] = {"level": 0, "type": None}

        for element in body:
            tag = element.tag.split("}")[-1] if "}" in element.tag else element.tag

            if tag == "p":
                para_md = self._convert_paragraph(element, list_state)
                if para_md is not None:
                    markdown_parts.append(para_md)
            elif tag == "tbl":
                if self._table_converter:
                    table_md = self._table_converter.convert(element)
                    markdown_parts.append(table_md)
            elif tag == "sectPr":
                # Ignore section properties
                pass

        result = "\n\n".join(filter(None, markdown_parts))

        # Final cleanup
        result = self._final_cleanup(result)

        return result

    def _final_cleanup(self, markdown: str) -> str:
        """Final Markdown cleanup."""
        # Remove empty headings (e.g., #### only lines)
        markdown = re.sub(r"^#{1,6}\s*$", "", markdown, flags=re.MULTILINE)

        # Limit consecutive blank lines to 2
        markdown = re.sub(r"\n{3,}", "\n\n", markdown)

        # Fix incorrect pmatrix usage (for conditional equations)
        markdown = re.sub(
            r"\\begin\{pmatrix\}(.+?)\\end\{pmatrix\}",
            self._fix_conditional_matrix,
            markdown,
            flags=re.DOTALL,
        )

        # Add space after Greek letter commands followed by alphabet
        for letter in GREEK_LETTERS:
            markdown = re.sub(rf"(\\{letter})([a-zA-Z_])", r"\1 \2", markdown)

        # Fix broken bold markup: merge consecutive bold markers
        def merge_bold_markers(text: str) -> str:
            pattern = r"\*\*([^*\n]+?)\*\*\*\*([^*\n]+?)\*\*"
            while re.search(pattern, text):
                text = re.sub(pattern, r"**\1\2**", text)
            return text

        markdown = merge_bold_markers(markdown)

        # Fix broken bold markup (**** to **) for remaining cases
        lines = markdown.split("\n")
        processed_lines = []
        for line in lines:
            line = re.sub(r"\*{4,}", "**", line)
            processed_lines.append(line)
        markdown = "\n".join(processed_lines)

        # Remove empty bold
        markdown = re.sub(r"(?<![a-zA-Z0-9_])\*\*\s+\*\*(?![a-zA-Z0-9_])", "", markdown)
        markdown = re.sub(r"(?<![a-zA-Z0-9_])\*\*\*\*(?![a-zA-Z0-9_])", "", markdown)

        return markdown.strip()

    def _fix_conditional_matrix(self, match: re.Match[str]) -> str:
        """Fix incorrect pmatrix usage for conditional equations."""
        content = match.group(1)

        # If conditional (contains ∀ or \forall), convert to parentheses
        if r"\forall" in content or "∀" in content:
            parts = content.split("&", 1)
            if len(parts) == 2:
                body = parts[0].strip()
                condition = parts[1].strip()
                return f"{body} \\quad {condition}"
            return content

        return match.group(0)

    def _convert_paragraph(self, para: ET.Element, list_state: dict[str, Any]) -> str:
        """Convert a paragraph."""
        pPr = para.find("w:pPr", NAMESPACES)

        heading_level = self._get_heading_level(pPr)
        is_list_item, list_type, list_level = self._check_list_item(pPr)
        content = self._get_paragraph_content(para)

        if not content.strip():
            return ""

        if heading_level:
            self._heading_count += 1
            if heading_level == 1:
                self._section_count += 1
            return f"{'#' * heading_level} {content}"

        if is_list_item:
            indent = "  " * list_level
            if list_type == "bullet":
                return f"{indent}- {content}"
            else:
                return f"{indent}1. {content}"

        return content

    def _get_heading_level(self, pPr: ET.Element | None) -> int:
        """Get heading level."""
        if pPr is None:
            return 0

        pStyle = pPr.find("w:pStyle", NAMESPACES)
        if pStyle is not None:
            style_id = pStyle.get(f"{{{NAMESPACES['w']}}}val", "")
            if style_id.startswith("Heading") or style_id.startswith("heading"):
                try:
                    return int(style_id[-1])
                except ValueError:
                    pass
            heading_map = {
                "1": 1,
                "2": 2,
                "3": 3,
                "4": 4,
                "5": 5,
                "6": 6,
                "Title": 1,
                "Subtitle": 2,
            }
            for key, level in heading_map.items():
                if key in style_id:
                    return level

        outlineLvl = pPr.find("w:outlineLvl", NAMESPACES)
        if outlineLvl is not None:
            val = outlineLvl.get(f"{{{NAMESPACES['w']}}}val")
            if val is not None:
                try:
                    return int(val) + 1
                except ValueError:
                    pass

        return 0

    def _check_list_item(self, pPr: ET.Element | None) -> tuple[bool, str | None, int]:
        """Check if the paragraph is a list item."""
        if pPr is None:
            return False, None, 0

        numPr = pPr.find("w:numPr", NAMESPACES)
        if numPr is not None:
            ilvl = numPr.find("w:ilvl", NAMESPACES)
            numId = numPr.find("w:numId", NAMESPACES)

            if numId is not None:
                level = 0
                if ilvl is not None:
                    val = ilvl.get(f"{{{NAMESPACES['w']}}}val")
                    if val:
                        try:
                            level = int(val)
                        except ValueError:
                            pass

                return True, "bullet", level

        return False, None, 0

    def _get_paragraph_content(self, para: ET.Element) -> str:
        """Get paragraph content."""
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
                math_text = self._convert_math(child)
                parts.append(math_text)
            elif tag == "oMathPara":
                math_para_text = self._convert_math_para(child)
                parts.append(math_para_text)

        return "".join(parts)

    def _convert_run(self, run: ET.Element) -> str:
        """Convert a run."""
        parts: list[str] = []
        rPr = run.find("w:rPr", NAMESPACES)

        is_bold = rPr is not None and rPr.find("w:b", NAMESPACES) is not None
        is_italic = rPr is not None and rPr.find("w:i", NAMESPACES) is not None
        is_strike = rPr is not None and rPr.find("w:strike", NAMESPACES) is not None
        is_code = rPr is not None and self._is_code_style(rPr)

        for child in run:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag

            if tag == "t":
                text = child.text or ""
                parts.append(text)
            elif tag == "br":
                parts.append("\n")
            elif tag == "tab":
                parts.append("\t")
            elif tag == "sym":
                parts.append(self._convert_symbol(child))

        text = "".join(parts)

        if text.strip():
            if is_code:
                text = f"`{text}`"
            else:
                if is_bold:
                    text = f"**{text}**"
                if is_italic:
                    text = f"*{text}*"
                if is_strike:
                    text = f"~~{text}~~"

        return text

    def _is_code_style(self, rPr: ET.Element) -> bool:
        """Check if code style."""
        rStyle = rPr.find("w:rStyle", NAMESPACES)
        if rStyle is not None:
            style_val = rStyle.get(f"{{{NAMESPACES['w']}}}val", "")
            if "code" in style_val.lower():
                return True

        rFonts = rPr.find("w:rFonts", NAMESPACES)
        if rFonts is not None:
            for attr in rFonts.attrib.values():
                if any(font in attr.lower() for font in ["courier", "consolas", "mono"]):
                    return True

        return False

    def _convert_symbol(self, sym: ET.Element) -> str:
        """Convert a symbol."""
        char = sym.get(f"{{{NAMESPACES['w']}}}char", "")
        if char:
            try:
                return chr(int(char, 16))
            except ValueError:
                pass
        return ""

    def _convert_hyperlink(self, hyperlink: ET.Element) -> str:
        """Convert a hyperlink."""
        text_parts: list[str] = []
        for run in hyperlink.findall(".//w:r", NAMESPACES):
            text_parts.append(self._convert_run(run))

        text = "".join(text_parts)
        return text

    def _convert_math(self, math: ET.Element) -> str:
        """Convert math to LaTeX format."""
        latex = self._omml_to_latex(math)
        if latex:
            latex = self._clean_equation_number(latex)
            return f"${latex}$"
        return ""

    def _convert_math_para(self, math_para: ET.Element) -> str:
        """Convert math paragraph to LaTeX format."""
        parts: list[str] = []
        for oMath in math_para.findall(".//m:oMath", NAMESPACES):
            latex = self._omml_to_latex(oMath)
            if latex:
                parts.append(latex)

        if parts:
            combined = " ".join(parts)
            combined = self._clean_equation_number(combined)

            eq_id = len(self._equations) + 1
            self._equations.append(
                EquationInfo(
                    id=eq_id,
                    latex=combined,
                    type="block",
                    line_number=self._current_line,
                )
            )

            if self.equation_numbers:
                self._equation_counter += 1
                return f"\n$$\n{combined} \\tag{{{self._equation_counter}}}\n$$\n"
            return f"\n$$\n{combined}\n$$\n"
        return ""

    def _omml_to_latex(self, element: ET.Element) -> str:
        """Convert OMML to LaTeX using math converter."""
        return self._math_converter.convert(element)

    def _clean_equation_number(self, latex: str) -> str:
        """Remove Word equation numbers and fix LaTeX syntax."""
        latex = re.sub(r"#\\left\(\s*SEQ\s+Equation\s*\\\*\s*ARABIC\s*\d+\\right\)", "", latex)
        latex = re.sub(r"#\(\s*SEQ\s+Equation\s*\*\s*ARABIC\s*\d+\)", "", latex)
        latex = self._fix_latex_spacing(latex)
        return latex.strip()

    def _fix_latex_spacing(self, latex: str) -> str:
        """Add proper spacing after LaTeX commands."""
        math_functions = [
            "lim",
            "sin",
            "cos",
            "tan",
            "cot",
            "sec",
            "csc",
            "arcsin",
            "arccos",
            "arctan",
            "sinh",
            "cosh",
            "tanh",
            "log",
            "ln",
            "exp",
            "det",
            "dim",
            "ker",
            "max",
            "min",
            "sup",
            "inf",
            "arg",
            "deg",
            "gcd",
            "hom",
            "mod",
        ]
        for func in math_functions:
            latex = re.sub(rf"(?<!\\)(?<![a-zA-Z])({func})(?![a-zA-Z])", rf"\\{func}", latex)

        latex = re.sub(r"(\\geq)([a-zA-Z{\\])", r"\1 \2", latex)
        latex = re.sub(r"(\\leq)([a-zA-Z{\\])", r"\1 \2", latex)
        latex = re.sub(r"(\\neq)([a-zA-Z{\\])", r"\1 \2", latex)
        latex = re.sub(r"(\\approx)([a-zA-Z{\\])", r"\1 \2", latex)
        latex = re.sub(r"(\d)(\\ldots)(\d|[a-zA-Z])", r"\1 \2 \3", latex)
        latex = re.sub(r"(\d)(\\cdots)(\d|[a-zA-Z])", r"\1 \2 \3", latex)
        latex = re.sub(r"(\\forall)([a-zA-Z{])", r"\1 \2", latex)
        latex = re.sub(r"(\\exists)([a-zA-Z{])", r"\1 \2", latex)
        latex = re.sub(r"(\\in)(\d)", r"\1 \2", latex)
        latex = re.sub(r"(\\in)([A-Z])", r"\1 \2", latex)
        latex = re.sub(r"(\\notin)([a-zA-Z{])", r"\1 \2", latex)
        latex = re.sub(r"(\\cup)([a-zA-Z{\\])", r"\1 \2", latex)
        latex = re.sub(r"(\\cap)([a-zA-Z{\\])", r"\1 \2", latex)
        latex = re.sub(r"(\\vee)([a-zA-Z{\\])", r"\1 \2", latex)
        latex = re.sub(r"(\\wedge)([a-zA-Z{\\])", r"\1 \2", latex)
        latex = re.sub(r"(\\subset)([a-zA-Z{\\])", r"\1 \2", latex)
        latex = re.sub(r"(\\supset)([a-zA-Z{\\])", r"\1 \2", latex)
        latex = re.sub(r"(\\partial)([a-zA-Z])", r"\1 \2", latex)

        for letter in GREEK_LETTERS:
            latex = re.sub(rf"(\\{letter})([a-zA-Z])", r"\1 \2", latex)

        return latex

    # Keep _escape_pipes_outside_math for backward compatibility with tests
    def _escape_pipes_outside_math(self, text: str) -> str:
        """Escape pipe characters outside of math expressions.

        Pipe characters inside $...$ are part of LaTeX and should not be escaped.
        """
        result: list[str] = []
        in_math = False
        i = 0

        while i < len(text):
            if text[i] == "$":
                in_math = not in_math
                result.append(text[i])
            elif text[i] == "|" and not in_math:
                result.append("\\|")
            else:
                result.append(text[i])
            i += 1

        return "".join(result)
