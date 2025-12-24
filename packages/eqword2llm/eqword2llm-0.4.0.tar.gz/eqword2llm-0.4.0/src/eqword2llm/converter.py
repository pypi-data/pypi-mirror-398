"""
eqword2llm: Equation-heavy Word document to Markdown conversion engine.

Converts OMML (Office Math Markup Language) to LaTeX format,
generating LLM-readable Markdown for scientific and technical documents.
"""

from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Literal
from xml.etree import ElementTree as ET

if TYPE_CHECKING:
    from typing import Any


@dataclass
class EquationInfo:
    """Information about an equation in the document."""

    id: int
    latex: str
    type: Literal["block", "inline"]
    line_number: int = 0


@dataclass
class DocumentMetadata:
    """Metadata about the converted document."""

    source: str
    equations: list[EquationInfo] = field(default_factory=list)
    section_count: int = 0
    equation_count: int = 0
    heading_count: int = 0

    def to_yaml(self) -> str:
        """Convert metadata to YAML frontmatter format."""
        lines = [
            "---",
            "format: eqword2llm/v1",
            f"source: {self.source}",
            "stats:",
            f"  sections: {self.section_count}",
            f"  equations: {self.equation_count}",
            f"  headings: {self.heading_count}",
        ]
        if self.equations:
            lines.append("equations:")
            for eq in self.equations:
                lines.append(f"  - id: {eq.id}")
                # Escape special characters in YAML
                escaped_latex = eq.latex.replace("\\", "\\\\").replace('"', '\\"')
                lines.append(f'    latex: "{escaped_latex}"')
                lines.append(f"    type: {eq.type}")
        lines.append("---")
        return "\n".join(lines)


@dataclass
class ConversionResult:
    """Result of document conversion."""

    markdown: str
    metadata: DocumentMetadata

    def to_structured(self) -> str:
        """Return Markdown with YAML frontmatter."""
        return f"{self.metadata.to_yaml()}\n\n{self.markdown}"

    def to_llm_prompt(self, instructions: str | None = None) -> str:
        """Generate LLM-ready prompt with document content."""
        default_instructions = """This document was converted from a Word file using eqword2llm.
Mathematical equations are formatted in LaTeX:
- Block equations: `$$...$$`
- Inline equations: `$...$`

Please analyze the content. If you need clarification about any equation or
concept, ask the user."""

        prompt_parts = [
            "# Document for Analysis",
            "",
            "## Document Information",
            f"- Source: {self.metadata.source}",
            f"- Equations: {self.metadata.equation_count}",
            f"- Sections: {self.metadata.section_count}",
            "",
            "## Content",
            "",
            self.markdown,
            "",
            "---",
            "",
            "## Instructions",
            "",
            instructions or default_instructions,
        ]
        return "\n".join(prompt_parts)

# Namespace definitions
NAMESPACES = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "pic": "http://schemas.openxmlformats.org/drawingml/2006/picture",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
    "wps": "http://schemas.microsoft.com/office/word/2010/wordprocessingShape",
}

# Register namespaces
for prefix, uri in NAMESPACES.items():
    ET.register_namespace(prefix, uri)

# Mathematical symbol mapping
SYMBOL_MAP = {
    "×": r"\times",
    "÷": r"\div",
    "±": r"\pm",
    "∓": r"\mp",
    "≤": r"\leq",
    "≥": r"\geq",
    "≠": r"\neq",
    "≈": r"\approx",
    "∞": r"\infty",
    "∑": r"\sum",
    "∏": r"\prod",
    "∫": r"\int",
    "∂": r"\partial",
    "∇": r"\nabla",
    "√": r"\sqrt",
    "∀": r"\forall ",
    "∈": r"\in ",
    "∉": r"\notin ",
    "⊂": r"\subset",
    "⊃": r"\supset",
    "⊆": r"\subseteq",
    "⊇": r"\supseteq",
    "∪": r"\cup",
    "∩": r"\cap",
    "∧": r"\wedge",
    "∨": r"\vee",
    "¬": r"\neg",
    "→": r"\rightarrow",
    "←": r"\leftarrow",
    "↔": r"\leftrightarrow",
    "⇒": r"\Rightarrow",
    "⇐": r"\Leftarrow",
    "⇔": r"\Leftrightarrow",
    "α": r"\alpha",
    "β": r"\beta",
    "γ": r"\gamma",
    "δ": r"\delta",
    "ε": r"\epsilon",
    "ζ": r"\zeta",
    "η": r"\eta",
    "θ": r"\theta",
    "ι": r"\iota",
    "κ": r"\kappa",
    "λ": r"\lambda",
    "μ": r"\mu",
    "ν": r"\nu",
    "ξ": r"\xi",
    "π": r"\pi",
    "ρ": r"\rho",
    "σ": r"\sigma",
    "τ": r"\tau",
    "υ": r"\upsilon",
    "φ": r"\phi",
    "χ": r"\chi",
    "ψ": r"\psi",
    "ω": r"\omega",
    "Α": r"\Alpha",
    "Β": r"\Beta",
    "Γ": r"\Gamma",
    "Δ": r"\Delta",
    "Ε": r"\Epsilon",
    "Ζ": r"\Zeta",
    "Η": r"\Eta",
    "Θ": r"\Theta",
    "Ι": r"\Iota",
    "Κ": r"\Kappa",
    "Λ": r"\Lambda",
    "Μ": r"\Mu",
    "Ν": r"\Nu",
    "Ξ": r"\Xi",
    "Π": r"\Pi",
    "Ρ": r"\Rho",
    "Σ": r"\Sigma",
    "Τ": r"\Tau",
    "Υ": r"\Upsilon",
    "Φ": r"\Phi",
    "Χ": r"\Chi",
    "Ψ": r"\Psi",
    "Ω": r"\Omega",
    "…": r"\ldots",
    "⋯": r"\cdots",
    "⋮": r"\vdots",
    "⋱": r"\ddots",
    "ℕ": r"\mathbb{N}",
    "ℤ": r"\mathbb{Z}",
    "ℚ": r"\mathbb{Q}",
    "ℝ": r"\mathbb{R}",
    "ℂ": r"\mathbb{C}",
}

# Greek letters list (for spacing correction)
GREEK_LETTERS = [
    "alpha",
    "beta",
    "gamma",
    "delta",
    "epsilon",
    "zeta",
    "eta",
    "theta",
    "iota",
    "kappa",
    "lambda",
    "mu",
    "nu",
    "xi",
    "pi",
    "rho",
    "sigma",
    "tau",
    "upsilon",
    "phi",
    "chi",
    "psi",
    "omega",
    "Gamma",
    "Delta",
    "Theta",
    "Lambda",
    "Xi",
    "Pi",
    "Sigma",
    "Phi",
    "Psi",
    "Omega",
]


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
                table_md = self._convert_table(element)
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

        # Fix broken bold markup (**** to **)
        markdown = re.sub(r"\*{4,}", "**", markdown)

        # Remove empty bold (** **)
        markdown = re.sub(r"\*\*\s*\*\*", "", markdown)

        return markdown.strip()

    def _fix_conditional_matrix(self, match: re.Match[str]) -> str:
        """Fix incorrect pmatrix usage for conditional equations."""
        content = match.group(1)

        # If conditional (contains ∀ or \forall), convert to parentheses
        if r"\forall" in content or "∀" in content:
            # Split by & - first part is body, rest is condition
            parts = content.split("&", 1)
            if len(parts) == 2:
                body = parts[0].strip()
                condition = parts[1].strip()
                return f"{body} \\quad {condition}"
            return content

        # Keep as-is for normal matrices
        return match.group(0)

    def _convert_paragraph(self, para: ET.Element, list_state: dict[str, Any]) -> str:
        """Convert a paragraph."""
        # Get paragraph properties
        pPr = para.find("w:pPr", NAMESPACES)

        # Check heading level
        heading_level = self._get_heading_level(pPr)

        # Check if list item
        is_list_item, list_type, list_level = self._check_list_item(pPr)

        # Get paragraph content
        content = self._get_paragraph_content(para)

        if not content.strip():
            return ""

        # If heading
        if heading_level:
            self._heading_count += 1
            if heading_level == 1:
                self._section_count += 1
            return f"{'#' * heading_level} {content}"

        # If list item
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
            # Check heading style
            if style_id.startswith("Heading") or style_id.startswith("heading"):
                try:
                    return int(style_id[-1])
                except ValueError:
                    pass
            # Japanese heading styles
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

        # Check outline level
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

                # Determine if numbered (simplified)
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

        # Check formatting
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
                # Symbol character
                parts.append(self._convert_symbol(child))

        text = "".join(parts)

        # Apply formatting
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

        # Check monospace font
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
            # Remove Word equation numbers
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
            # Remove Word equation numbers
            combined = self._clean_equation_number(combined)

            # Track equation metadata
            eq_id = len(self._equations) + 1
            self._equations.append(
                EquationInfo(
                    id=eq_id,
                    latex=combined,
                    type="block",
                    line_number=self._current_line,
                )
            )

            # Add equation number if enabled
            if self.equation_numbers:
                self._equation_counter += 1
                return f"\n$$\n{combined} \\tag{{{self._equation_counter}}}\n$$\n"
            return f"\n$$\n{combined}\n$$\n"
        return ""

    def _clean_equation_number(self, latex: str) -> str:
        """Remove Word equation numbers and fix LaTeX syntax."""
        # Remove patterns like #( SEQ Equation * ARABIC N)
        latex = re.sub(r"#\\left\(\s*SEQ\s+Equation\s*\\\*\s*ARABIC\s*\d+\\right\)", "", latex)
        latex = re.sub(r"#\(\s*SEQ\s+Equation\s*\*\s*ARABIC\s*\d+\)", "", latex)

        # Fix LaTeX syntax
        latex = self._fix_latex_spacing(latex)

        return latex.strip()

    def _fix_latex_spacing(self, latex: str) -> str:
        """Add proper spacing after LaTeX commands."""
        # Convert common math function names to LaTeX commands
        # Must be done before other transformations
        math_functions = [
            "lim", "sin", "cos", "tan", "cot", "sec", "csc",
            "arcsin", "arccos", "arctan", "sinh", "cosh", "tanh",
            "log", "ln", "exp", "det", "dim", "ker", "max", "min",
            "sup", "inf", "arg", "deg", "gcd", "hom", "mod",
        ]
        for func in math_functions:
            # Match function name not already preceded by backslash
            # Also match at start of string or after non-letter characters
            latex = re.sub(rf"(?<!\\)(?<![a-zA-Z])({func})(?![a-zA-Z])", rf"\\{func}", latex)

        # Add space after comparison operators
        latex = re.sub(r"(\\geq)([a-zA-Z{\\])", r"\1 \2", latex)
        latex = re.sub(r"(\\leq)([a-zA-Z{\\])", r"\1 \2", latex)
        latex = re.sub(r"(\\neq)([a-zA-Z{\\])", r"\1 \2", latex)
        latex = re.sub(r"(\\approx)([a-zA-Z{\\])", r"\1 \2", latex)

        # Add space around \ldots, \cdots
        latex = re.sub(r"(\d)(\\ldots)(\d|[a-zA-Z])", r"\1 \2 \3", latex)
        latex = re.sub(r"(\d)(\\cdots)(\d|[a-zA-Z])", r"\1 \2 \3", latex)

        # Ensure space after \forall, \exists
        latex = re.sub(r"(\\forall)([a-zA-Z{])", r"\1 \2", latex)
        latex = re.sub(r"(\\exists)([a-zA-Z{])", r"\1 \2", latex)

        # Ensure space after \in, \notin
        latex = re.sub(r"(\\in)(\d)", r"\1 \2", latex)
        latex = re.sub(r"(\\in)([A-Z])", r"\1 \2", latex)
        latex = re.sub(r"(\\notin)([a-zA-Z{])", r"\1 \2", latex)

        # Add space after set operators
        latex = re.sub(r"(\\cup)([a-zA-Z{\\])", r"\1 \2", latex)
        latex = re.sub(r"(\\cap)([a-zA-Z{\\])", r"\1 \2", latex)
        latex = re.sub(r"(\\vee)([a-zA-Z{\\])", r"\1 \2", latex)
        latex = re.sub(r"(\\wedge)([a-zA-Z{\\])", r"\1 \2", latex)
        latex = re.sub(r"(\\subset)([a-zA-Z{\\])", r"\1 \2", latex)
        latex = re.sub(r"(\\supset)([a-zA-Z{\\])", r"\1 \2", latex)

        # Add space after \partial when followed by letter
        latex = re.sub(r"(\\partial)([a-zA-Z])", r"\1 \2", latex)

        # Add space after Greek letter commands followed by alphabet
        for letter in GREEK_LETTERS:
            latex = re.sub(rf"(\\{letter})([a-zA-Z])", r"\1 \2", latex)

        return latex

    def _omml_to_latex(self, element: ET.Element) -> str:
        """Convert OMML (Office Math Markup Language) to LaTeX."""
        result: list[str] = []

        for child in element:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag

            if tag == "r":
                text = self._get_math_text(child)
                result.append(text)
            elif tag == "f":
                result.append(self._convert_fraction(child))
            elif tag == "rad":
                result.append(self._convert_radical(child))
            elif tag == "sSup":
                result.append(self._convert_superscript(child))
            elif tag == "sSub":
                result.append(self._convert_subscript(child))
            elif tag == "sSubSup":
                result.append(self._convert_subsup(child))
            elif tag == "nary":
                result.append(self._convert_nary(child))
            elif tag == "d":
                result.append(self._convert_delimiter(child))
            elif tag == "func":
                result.append(self._convert_function(child))
            elif tag == "eqArr":
                result.append(self._convert_eq_array(child))
            elif tag == "m":
                result.append(self._convert_matrix(child))
            elif tag == "limLow":
                result.append(self._convert_lim_low(child))
            elif tag == "limUpp":
                result.append(self._convert_lim_upp(child))
            elif tag == "acc":
                result.append(self._convert_accent(child))
            elif tag == "bar":
                result.append(self._convert_bar(child))
            elif tag == "box":
                result.append(self._omml_to_latex(child))
            elif tag == "groupChr":
                result.append(self._convert_group_chr(child))
            elif tag == "borderBox":
                result.append(self._omml_to_latex(child))
            else:
                nested = self._omml_to_latex(child)
                if nested:
                    result.append(nested)

        return "".join(result)

    def _get_math_text(self, run: ET.Element) -> str:
        """Get text from math run."""
        text_parts: list[str] = []
        for t in run.findall(".//m:t", NAMESPACES):
            if t.text:
                text_parts.append(self._escape_latex(t.text))
        return "".join(text_parts)

    def _escape_latex(self, text: str) -> str:
        """Escape or convert LaTeX special characters."""
        for char, latex in SYMBOL_MAP.items():
            text = text.replace(char, latex)
        return text

    def _convert_fraction(self, frac: ET.Element) -> str:
        """Convert fraction."""
        # Check fraction type (bar, noBar, skw, lin)
        frac_pr = frac.find("m:fPr", NAMESPACES)
        frac_type = "bar"  # default
        if frac_pr is not None:
            type_elem = frac_pr.find("m:type", NAMESPACES)
            if type_elem is not None:
                frac_type = type_elem.get(f"{{{NAMESPACES['m']}}}val", "bar")

        num = frac.find("m:num", NAMESPACES)
        den = frac.find("m:den", NAMESPACES)

        num_latex = self._omml_to_latex(num) if num is not None else ""
        den_latex = self._omml_to_latex(den) if den is not None else ""

        # noBar type is typically used for binomial coefficients
        if frac_type == "noBar":
            return rf"\binom{{{num_latex}}}{{{den_latex}}}"

        return rf"\frac{{{num_latex}}}{{{den_latex}}}"

    def _convert_radical(self, rad: ET.Element) -> str:
        """Convert radical (square root)."""
        deg = rad.find("m:deg", NAMESPACES)
        e = rad.find("m:e", NAMESPACES)

        e_latex = self._omml_to_latex(e) if e is not None else ""

        if deg is not None:
            deg_latex = self._omml_to_latex(deg)
            if deg_latex and deg_latex.strip():
                return rf"\sqrt[{deg_latex}]{{{e_latex}}}"

        return rf"\sqrt{{{e_latex}}}"

    def _convert_superscript(self, ssup: ET.Element) -> str:
        """Convert superscript."""
        e = ssup.find("m:e", NAMESPACES)
        sup = ssup.find("m:sup", NAMESPACES)

        e_latex = self._omml_to_latex(e) if e is not None else ""
        sup_latex = self._omml_to_latex(sup) if sup is not None else ""

        if len(e_latex) > 1 and not (e_latex.startswith("{") and e_latex.endswith("}")):
            e_latex = f"{{{e_latex}}}"

        return f"{e_latex}^{{{sup_latex}}}"

    def _convert_subscript(self, ssub: ET.Element) -> str:
        """Convert subscript."""
        e = ssub.find("m:e", NAMESPACES)
        sub = ssub.find("m:sub", NAMESPACES)

        e_latex = self._omml_to_latex(e) if e is not None else ""
        sub_latex = self._omml_to_latex(sub) if sub is not None else ""

        if len(e_latex) > 1 and not (e_latex.startswith("{") and e_latex.endswith("}")):
            e_latex = f"{{{e_latex}}}"

        return f"{e_latex}_{{{sub_latex}}}"

    def _convert_subsup(self, ssubsup: ET.Element) -> str:
        """Convert subscript-superscript."""
        e = ssubsup.find("m:e", NAMESPACES)
        sub = ssubsup.find("m:sub", NAMESPACES)
        sup = ssubsup.find("m:sup", NAMESPACES)

        e_latex = self._omml_to_latex(e) if e is not None else ""
        sub_latex = self._omml_to_latex(sub) if sub is not None else ""
        sup_latex = self._omml_to_latex(sup) if sup is not None else ""

        if len(e_latex) > 1 and not (e_latex.startswith("{") and e_latex.endswith("}")):
            e_latex = f"{{{e_latex}}}"

        return f"{e_latex}_{{{sub_latex}}}^{{{sup_latex}}}"

    def _convert_nary(self, nary: ET.Element) -> str:
        """Convert n-ary operator (integral, summation, etc.)."""
        naryPr = nary.find("m:naryPr", NAMESPACES)
        sub = nary.find("m:sub", NAMESPACES)
        sup = nary.find("m:sup", NAMESPACES)
        e = nary.find("m:e", NAMESPACES)

        operator = r"\int"  # Default
        if naryPr is not None:
            chr_elem = naryPr.find("m:chr", NAMESPACES)
            if chr_elem is not None:
                char = chr_elem.get(f"{{{NAMESPACES['m']}}}val", "")
                operator_map = {
                    "∑": r"\sum",
                    "∏": r"\prod",
                    "∫": r"\int",
                    "∬": r"\iint",
                    "∭": r"\iiint",
                    "∮": r"\oint",
                    "⋃": r"\bigcup",
                    "⋂": r"\bigcap",
                }
                operator = operator_map.get(char, operator)

        sub_latex = self._omml_to_latex(sub) if sub is not None else ""
        sup_latex = self._omml_to_latex(sup) if sup is not None else ""
        e_latex = self._omml_to_latex(e) if e is not None else ""

        result = operator
        if sub_latex:
            result += f"_{{{sub_latex}}}"
        if sup_latex:
            result += f"^{{{sup_latex}}}"
        result += f" {e_latex}"

        return result

    def _convert_delimiter(self, delim: ET.Element) -> str:
        """Convert delimiter (parentheses, brackets, etc.)."""
        dPr = delim.find("m:dPr", NAMESPACES)

        beg_chr = "("
        end_chr = ")"

        if dPr is not None:
            begChr = dPr.find("m:begChr", NAMESPACES)
            endChr = dPr.find("m:endChr", NAMESPACES)

            if begChr is not None:
                beg_chr = begChr.get(f"{{{NAMESPACES['m']}}}val", "(")
            if endChr is not None:
                end_chr = endChr.get(f"{{{NAMESPACES['m']}}}val", ")")

        # Check if content contains a matrix - if so, use appropriate matrix environment
        e_elements = delim.findall("m:e", NAMESPACES)
        if len(e_elements) == 1:
            first_e = e_elements[0]
            matrix = first_e.find("m:m", NAMESPACES)
            if matrix is not None:
                # Convert matrix with appropriate environment based on delimiters
                matrix_content = self._convert_matrix_content(matrix)
                env = self._get_matrix_environment(beg_chr, end_chr)
                return rf"\begin{{{env}}}{matrix_content}\end{{{env}}}"

            # Check if content is a noBar fraction (binomial coefficient)
            # In this case, the delimiter parentheses are redundant
            frac = first_e.find("m:f", NAMESPACES)
            if frac is not None and beg_chr == "(" and end_chr == ")":
                frac_pr = frac.find("m:fPr", NAMESPACES)
                if frac_pr is not None:
                    type_elem = frac_pr.find("m:type", NAMESPACES)
                    if type_elem is not None:
                        frac_type = type_elem.get(f"{{{NAMESPACES['m']}}}val", "bar")
                        if frac_type == "noBar":
                            # Return just the binomial, without extra parentheses
                            return self._convert_fraction(frac)

        beg_map = {
            "(": r"\left(",
            "[": r"\left[",
            "{": r"\left\{",
            "|": r"\left|",
            "⟨": r"\left\langle",
            "‖": r"\left\|",
            "": "",
        }
        end_map = {
            ")": r"\right)",
            "]": r"\right]",
            "}": r"\right\}",
            "|": r"\right|",
            "⟩": r"\right\rangle",
            "‖": r"\right\|",
            "": r"\right.",
        }

        beg = beg_map.get(beg_chr, rf"\left{beg_chr}")
        end = end_map.get(end_chr, rf"\right{end_chr}")

        content_parts: list[str] = []
        for e in e_elements:
            content_parts.append(self._omml_to_latex(e))

        content = ", ".join(content_parts)

        return f"{beg}{content}{end}"

    def _get_matrix_environment(self, beg_chr: str, end_chr: str) -> str:
        """Get appropriate LaTeX matrix environment based on delimiters."""
        if beg_chr == "[" and end_chr == "]":
            return "bmatrix"
        elif beg_chr == "(" and end_chr == ")":
            return "pmatrix"
        elif beg_chr == "{" and end_chr == "}":
            return "Bmatrix"
        elif beg_chr == "|" and end_chr == "|":
            return "vmatrix"
        elif beg_chr == "‖" and end_chr == "‖":
            return "Vmatrix"
        else:
            return "matrix"

    def _convert_matrix_content(self, matrix: ET.Element) -> str:
        """Convert matrix content without environment wrapper."""
        rows: list[str] = []
        for mr in matrix.findall("m:mr", NAMESPACES):
            cols: list[str] = []
            for e in mr.findall("m:e", NAMESPACES):
                cols.append(self._omml_to_latex(e))
            rows.append(" & ".join(cols))
        return r" \\ ".join(rows)

    def _convert_function(self, func: ET.Element) -> str:
        """Convert function."""
        fName = func.find("m:fName", NAMESPACES)
        e = func.find("m:e", NAMESPACES)

        func_name = self._omml_to_latex(fName) if fName is not None else ""
        e_latex = self._omml_to_latex(e) if e is not None else ""

        func_map = {
            "sin": r"\sin",
            "cos": r"\cos",
            "tan": r"\tan",
            "cot": r"\cot",
            "sec": r"\sec",
            "csc": r"\csc",
            "sinh": r"\sinh",
            "cosh": r"\cosh",
            "tanh": r"\tanh",
            "log": r"\log",
            "ln": r"\ln",
            "exp": r"\exp",
            "lim": r"\lim",
            "max": r"\max",
            "min": r"\min",
            "sup": r"\sup",
            "inf": r"\inf",
            "det": r"\det",
            "dim": r"\dim",
            "arg": r"\arg",
        }

        latex_func = func_map.get(func_name.strip().lower(), func_name)

        return f"{latex_func} {e_latex}"

    def _convert_eq_array(self, eq_arr: ET.Element) -> str:
        """Convert equation array."""
        rows: list[str] = []
        for e in eq_arr.findall("m:e", NAMESPACES):
            rows.append(self._omml_to_latex(e))

        if len(rows) > 1:
            return r"\begin{aligned}" + r" \\ ".join(rows) + r"\end{aligned}"
        return rows[0] if rows else ""

    def _convert_matrix(self, matrix: ET.Element) -> str:
        """Convert matrix."""
        rows: list[str] = []
        for mr in matrix.findall("m:mr", NAMESPACES):
            cols: list[str] = []
            for e in mr.findall("m:e", NAMESPACES):
                cols.append(self._omml_to_latex(e))
            rows.append(" & ".join(cols))

        return r"\begin{pmatrix}" + r" \\ ".join(rows) + r"\end{pmatrix}"

    def _convert_lim_low(self, lim_low: ET.Element) -> str:
        """Convert lower limit."""
        e = lim_low.find("m:e", NAMESPACES)
        lim = lim_low.find("m:lim", NAMESPACES)

        e_latex = self._omml_to_latex(e) if e is not None else ""
        lim_latex = self._omml_to_latex(lim) if lim is not None else ""

        return f"{e_latex}_{{{lim_latex}}}"

    def _convert_lim_upp(self, lim_upp: ET.Element) -> str:
        """Convert upper limit."""
        e = lim_upp.find("m:e", NAMESPACES)
        lim = lim_upp.find("m:lim", NAMESPACES)

        e_latex = self._omml_to_latex(e) if e is not None else ""
        lim_latex = self._omml_to_latex(lim) if lim is not None else ""

        return f"{e_latex}^{{{lim_latex}}}"

    def _convert_accent(self, acc: ET.Element) -> str:
        """Convert accent."""
        accPr = acc.find("m:accPr", NAMESPACES)
        e = acc.find("m:e", NAMESPACES)

        e_latex = self._omml_to_latex(e) if e is not None else ""

        accent_char = "^"  # Default
        if accPr is not None:
            chr_elem = accPr.find("m:chr", NAMESPACES)
            if chr_elem is not None:
                accent_char = chr_elem.get(f"{{{NAMESPACES['m']}}}val", "^")

        accent_map = {
            "̂": r"\hat",
            "̃": r"\tilde",
            "̄": r"\bar",
            "́": r"\acute",
            "̀": r"\grave",
            "̇": r"\dot",
            "̈": r"\ddot",
            "̆": r"\breve",
            "̌": r"\check",
            "⃗": r"\vec",
            "^": r"\hat",
            "~": r"\tilde",
            "¯": r"\bar",
            "→": r"\vec",
        }

        latex_accent = accent_map.get(accent_char, r"\hat")

        return f"{latex_accent}{{{e_latex}}}"

    def _convert_bar(self, bar: ET.Element) -> str:
        """Convert bar (overline)."""
        e = bar.find("m:e", NAMESPACES)
        e_latex = self._omml_to_latex(e) if e is not None else ""

        return rf"\overline{{{e_latex}}}"

    def _convert_group_chr(self, group_chr: ET.Element) -> str:
        """Convert group character."""
        e = group_chr.find("m:e", NAMESPACES)
        e_latex = self._omml_to_latex(e) if e is not None else ""

        groupChrPr = group_chr.find("m:groupChrPr", NAMESPACES)
        if groupChrPr is not None:
            chr_elem = groupChrPr.find("m:chr", NAMESPACES)
            if chr_elem is not None:
                char = chr_elem.get(f"{{{NAMESPACES['m']}}}val", "")
                if char == "⏟":
                    return rf"\underbrace{{{e_latex}}}"
                elif char == "⏞":
                    return rf"\overbrace{{{e_latex}}}"

        return e_latex

    def _convert_table(self, table: ET.Element) -> str:
        """Convert table."""
        rows: list[str] = []
        header_done = False

        for tr in table.findall(".//w:tr", NAMESPACES):
            cells: list[str] = []
            for tc in tr.findall(".//w:tc", NAMESPACES):
                cell_text: list[str] = []
                for p in tc.findall(".//w:p", NAMESPACES):
                    cell_text.append(self._get_paragraph_content(p))
                cells.append(" ".join(cell_text).replace("\n", "<br>"))

            if cells:
                rows.append("| " + " | ".join(cells) + " |")

                # Add separator after header row
                if not header_done:
                    rows.append("| " + " | ".join(["---"] * len(cells)) + " |")
                    header_done = True

        return "\n".join(rows)
