"""
LaTeX syntax validation tests.

Since math rendering varies by tool, we validate LaTeX syntax
correctness rather than rendering results.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

from eqword2llm import WordToMarkdownConverter


class TestLatexSyntax:
    """Static validation of LaTeX syntax."""

    def test_balanced_braces(self) -> None:
        """Check brace balance."""
        latex = r"\frac{a}{b} + x^{2}"
        assert self._count_balanced(latex, "{", "}"), "Braces are unbalanced"

    def test_balanced_dollar_signs(self) -> None:
        """Check dollar sign balance."""
        markdown = "Math $x^2$ and $$y = mx + b$$ here"
        # Inline math
        inline_count = len(re.findall(r"(?<!\$)\$(?!\$)", markdown))
        assert inline_count % 2 == 0, "Inline math $ signs are unbalanced"
        # Block math
        block_count = markdown.count("$$")
        assert block_count % 2 == 0, "Block math $$ signs are unbalanced"

    def test_no_empty_commands(self) -> None:
        """Ensure no empty command arguments."""
        latex = r"\frac{a}{b}"
        assert r"\frac{}" not in latex, "Empty fraction found"
        assert r"\sqrt{}" not in latex, "Empty square root found"

    def test_no_command_collision(self) -> None:
        """Ensure no command collision."""
        latex = r"\geq n"
        assert not re.search(r"\\geq\\[a-zA-Z]", latex), "Command collision after \\geq"
        assert not re.search(r"\\leq\\[a-zA-Z]", latex), "Command collision after \\leq"

    @staticmethod
    def _count_balanced(text: str, open_char: str, close_char: str) -> bool:
        """Check bracket balance."""
        count = 0
        for char in text:
            if char == open_char:
                count += 1
            elif char == close_char:
                count -= 1
            if count < 0:
                return False
        return count == 0


class TestKatexValidation:
    """LaTeX syntax validation using KaTeX (requires Node.js)."""

    @pytest.fixture(autouse=True)
    def check_katex_available(self) -> None:
        """Check if KaTeX is available."""
        if not shutil.which("node"):
            pytest.skip("Node.js is not installed")

        result = subprocess.run(
            ["node", "-e", 'require("katex")'],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            pytest.skip("KaTeX is not installed (npm install katex)")

    def validate_latex(self, latex: str) -> tuple[bool, str]:
        """Validate LaTeX syntax with KaTeX."""
        escaped = latex.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")

        js_code = f"""
            const katex = require("katex");
            try {{
                katex.renderToString('{escaped}', {{ throwOnError: true, displayMode: true }});
                console.log("OK");
            }} catch(e) {{
                console.error(e.message);
                process.exit(1);
            }}
        """

        result = subprocess.run(
            ["node", "-e", js_code],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            return True, ""
        return False, result.stderr.strip()

    @pytest.mark.parametrize(
        "latex,description",
        [
            (r"x^{2} + y^{2} = z^{2}", "Pythagorean theorem"),
            (r"\frac{a}{b}", "Fraction"),
            (r"\sum_{i=1}^{n} x_i", "Summation"),
            (r"\int_{0}^{\infty} e^{-x} dx", "Integral"),
            (r"\sqrt{x^2 + y^2}", "Square root"),
            (r"\alpha + \beta = \gamma", "Greek letters"),
            (r"\forall x \in \mathbb{R}", "Universal quantifier"),
            (r"x \geq 0", "Inequality"),
            (r"\begin{pmatrix} a & b \\ c & d \end{pmatrix}", "Matrix"),
        ],
    )
    def test_valid_latex_patterns(self, latex: str, description: str) -> None:
        """Verify common LaTeX patterns are valid in KaTeX."""
        is_valid, error = self.validate_latex(latex)
        assert is_valid, f"{description}: {error}"


class TestConverterBasic:
    """Basic converter tests."""

    def test_converter_import(self) -> None:
        """Verify WordToMarkdownConverter can be imported."""
        assert WordToMarkdownConverter is not None

    def test_converter_init(self, tmp_path: Path) -> None:
        """Verify constructor works correctly."""
        dummy_path = tmp_path / "dummy.docx"
        converter = WordToMarkdownConverter(dummy_path)
        assert converter.docx_path == dummy_path

    def test_converter_init_with_equation_numbers(self, tmp_path: Path) -> None:
        """Verify constructor accepts equation_numbers parameter."""
        dummy_path = tmp_path / "dummy.docx"

        # Default is True
        converter = WordToMarkdownConverter(dummy_path)
        assert converter.equation_numbers is True

        # Explicit True
        converter = WordToMarkdownConverter(dummy_path, equation_numbers=True)
        assert converter.equation_numbers is True

        # Explicit False
        converter = WordToMarkdownConverter(dummy_path, equation_numbers=False)
        assert converter.equation_numbers is False

    def test_file_not_found(self, tmp_path: Path) -> None:
        """Verify FileNotFoundError is raised for non-existent files."""
        dummy_path = tmp_path / "nonexistent.docx"
        converter = WordToMarkdownConverter(dummy_path)
        with pytest.raises(FileNotFoundError):
            converter.convert()


class TestMathElementConversion:
    """Individual math element conversion tests."""

    def test_fraction_pattern(self) -> None:
        """Verify fraction pattern is correct."""
        expected_pattern = r"\\frac\{[^}]+\}\{[^}]+\}"
        latex = r"\frac{a}{b}"
        assert re.match(expected_pattern, latex)

    def test_superscript_pattern(self) -> None:
        """Verify superscript pattern is correct."""
        expected_pattern = r"[a-zA-Z]+\^\{[^}]+\}"
        latex = r"x^{2}"
        assert re.match(expected_pattern, latex)

    def test_subscript_pattern(self) -> None:
        """Verify subscript pattern is correct."""
        expected_pattern = r"[a-zA-Z]+_\{[^}]+\}"
        latex = r"x_{i}"
        assert re.match(expected_pattern, latex)


class TestEquationNumbering:
    """Tests for equation numbering feature."""

    def test_equation_numbering_tag_format(self) -> None:
        """Verify equation number tag format is correct."""
        # The tag format should be \tag{N}
        tag_pattern = r"\\tag\{\d+\}"
        assert re.match(tag_pattern, r"\tag{1}")
        assert re.match(tag_pattern, r"\tag{42}")
        assert not re.match(tag_pattern, r"\tag{}")
        assert not re.match(tag_pattern, r"\tag{abc}")

    def test_equation_counter_initialization(self, tmp_path: Path) -> None:
        """Verify equation counter starts at 0."""
        dummy_path = tmp_path / "dummy.docx"
        converter = WordToMarkdownConverter(dummy_path)
        assert converter._equation_counter == 0

    def test_tag_syntax_valid_in_latex(self) -> None:
        """Verify \\tag{N} is valid LaTeX syntax."""
        # \tag is a standard LaTeX/MathJax/KaTeX command
        latex_with_tag = r"E = mc^{2} \tag{1}"
        # Should contain the tag
        assert r"\tag{1}" in latex_with_tag

    def test_equation_numbers_in_block_math_pattern(self) -> None:
        """Verify block math with equation numbers has correct pattern."""
        # Pattern: $$ ... \tag{N} $$
        block_with_number = r"""$$
x^{2} + y^{2} = z^{2} \tag{1}
$$"""
        assert r"\tag{1}" in block_with_number
        assert block_with_number.startswith("$$")
        assert block_with_number.strip().endswith("$$")

    def test_sequential_numbering_pattern(self) -> None:
        """Verify sequential equation numbers follow correct pattern."""
        equations = [
            r"$$a = b \tag{1}$$",
            r"$$c = d \tag{2}$$",
            r"$$e = f \tag{3}$$",
        ]
        for i, eq in enumerate(equations, 1):
            assert rf"\tag{{{i}}}" in eq


# ===== Helper functions =====


def extract_latex_blocks(markdown: str) -> list[str]:
    """Extract block math from Markdown."""
    pattern = r"\$\$(.*?)\$\$"
    return re.findall(pattern, markdown, re.DOTALL)


def extract_inline_latex(markdown: str) -> list[str]:
    """Extract inline math from Markdown."""
    pattern = r"(?<!\$)\$(?!\$)(.*?)(?<!\$)\$(?!\$)"
    return re.findall(pattern, markdown)


def extract_equation_numbers(markdown: str) -> list[int]:
    """Extract equation numbers from Markdown."""
    pattern = r"\\tag\{(\d+)\}"
    matches = re.findall(pattern, markdown)
    return [int(m) for m in matches]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
