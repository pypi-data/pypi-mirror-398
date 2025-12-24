"""
Integration tests using actual Word files.

Tests conversion of real .docx files to verify end-to-end functionality.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from eqword2llm import WordToMarkdownConverter

# Path to test fixtures
FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestWordFileConversion:
    """Integration tests for Word file conversion."""

    @pytest.fixture
    def math_docx_path(self) -> Path:
        """Path to sample Word file with math equations."""
        return FIXTURES_DIR / "sample_with_math.docx"

    @pytest.fixture
    def unicode_docx_path(self) -> Path:
        """Path to sample Word file with multilingual content."""
        return FIXTURES_DIR / "sample_unicode.docx"

    def test_math_file_exists(self, math_docx_path: Path) -> None:
        """Verify test fixture file exists."""
        assert math_docx_path.exists(), f"Test fixture not found: {math_docx_path}"

    def test_unicode_file_exists(self, unicode_docx_path: Path) -> None:
        """Verify test fixture file exists."""
        assert unicode_docx_path.exists(), f"Test fixture not found: {unicode_docx_path}"

    def test_convert_math_document(self, math_docx_path: Path) -> None:
        """Test conversion of document with math equations."""
        converter = WordToMarkdownConverter(math_docx_path)
        markdown = converter.convert()

        # Verify basic structure
        assert len(markdown) > 0, "Conversion produced empty output"

        # Verify headings are present
        assert "# Sample Math Document" in markdown or "Sample Math Document" in markdown

        # Verify block math equations exist
        assert "$$" in markdown, "No block equations found"

    def test_math_document_has_equations(self, math_docx_path: Path) -> None:
        """Verify math equations are converted to LaTeX."""
        converter = WordToMarkdownConverter(math_docx_path)
        markdown = converter.convert()

        # Extract block equations
        block_equations = re.findall(r"\$\$(.*?)\$\$", markdown, re.DOTALL)
        assert len(block_equations) > 0, "No block equations extracted"

        # Check for expected math patterns
        all_equations = " ".join(block_equations)

        # Should have superscripts (a^2, b^2, c^2)
        assert "^{" in all_equations or "^2" in all_equations, "No superscripts found"

    def test_math_document_has_fractions(self, math_docx_path: Path) -> None:
        """Verify fractions are converted correctly."""
        converter = WordToMarkdownConverter(math_docx_path)
        markdown = converter.convert()

        # Should contain \frac command
        assert r"\frac" in markdown, "No fractions found"

    def test_math_document_has_greek_letters(self, math_docx_path: Path) -> None:
        """Verify Greek letters are converted to LaTeX."""
        converter = WordToMarkdownConverter(math_docx_path)
        markdown = converter.convert()

        # Should contain Greek letter commands
        greek_patterns = [r"\alpha", r"\beta", r"\gamma"]
        found_greek = any(pattern in markdown for pattern in greek_patterns)
        assert found_greek, "No Greek letters found"

    def test_math_document_equation_numbers(self, math_docx_path: Path) -> None:
        """Verify equation numbers are added by default."""
        converter = WordToMarkdownConverter(math_docx_path, equation_numbers=True)
        markdown = converter.convert()

        # Should contain \tag{N} for equation numbers
        tag_pattern = r"\\tag\{\d+\}"
        tags = re.findall(tag_pattern, markdown)
        assert len(tags) > 0, "No equation numbers found"

        # Numbers should be sequential
        numbers = [int(re.search(r"\d+", tag).group()) for tag in tags]
        assert numbers == list(range(1, len(numbers) + 1)), "Equation numbers not sequential"

    def test_math_document_no_equation_numbers(self, math_docx_path: Path) -> None:
        """Verify equation numbers can be disabled."""
        converter = WordToMarkdownConverter(math_docx_path, equation_numbers=False)
        markdown = converter.convert()

        # Should NOT contain \tag{N}
        assert r"\tag{" not in markdown, "Equation numbers found when disabled"

    def test_convert_unicode_document(self, unicode_docx_path: Path) -> None:
        """Test conversion of document with multilingual content."""
        converter = WordToMarkdownConverter(unicode_docx_path)
        markdown = converter.convert()

        # Verify basic structure
        assert len(markdown) > 0, "Conversion produced empty output"

    def test_unicode_document_japanese(self, unicode_docx_path: Path) -> None:
        """Verify Japanese text is preserved."""
        converter = WordToMarkdownConverter(unicode_docx_path)
        markdown = converter.convert()

        # Japanese text should be present
        assert "日本語" in markdown, "Japanese text not found"
        assert "テスト" in markdown or "です" in markdown, "Japanese content not preserved"

    def test_unicode_document_chinese(self, unicode_docx_path: Path) -> None:
        """Verify Chinese text is preserved."""
        converter = WordToMarkdownConverter(unicode_docx_path)
        markdown = converter.convert()

        # Chinese text should be present
        assert "中文" in markdown, "Chinese text not found"

    def test_unicode_document_korean(self, unicode_docx_path: Path) -> None:
        """Verify Korean text is preserved."""
        converter = WordToMarkdownConverter(unicode_docx_path)
        markdown = converter.convert()

        # Korean text should be present
        assert "한국어" in markdown or "한글" in markdown, "Korean text not found"

    def test_unicode_document_with_math(self, unicode_docx_path: Path) -> None:
        """Verify math equations work with multilingual content."""
        converter = WordToMarkdownConverter(unicode_docx_path)
        markdown = converter.convert()

        # Should have both Unicode text and math
        assert "日本語" in markdown, "Japanese text not found"
        assert "$$" in markdown or "$" in markdown, "No math equations found"


class TestConversionOutput:
    """Tests for conversion output format."""

    @pytest.fixture
    def math_docx_path(self) -> Path:
        """Path to sample Word file with math equations."""
        return FIXTURES_DIR / "sample_with_math.docx"

    def test_output_is_valid_markdown(self, math_docx_path: Path) -> None:
        """Verify output is valid Markdown structure."""
        converter = WordToMarkdownConverter(math_docx_path)
        markdown = converter.convert()

        # Check for common Markdown elements
        lines = markdown.split("\n")

        # Should have non-empty lines
        non_empty_lines = [line for line in lines if line.strip()]
        assert len(non_empty_lines) > 0, "No content in output"

    def test_block_math_format(self, math_docx_path: Path) -> None:
        """Verify block math has correct format."""
        converter = WordToMarkdownConverter(math_docx_path, equation_numbers=False)
        markdown = converter.convert()

        # Block math should be on separate lines
        # Pattern: newline, $$, content, $$, newline
        block_pattern = r"\n\$\$\n.*?\n\$\$\n"
        blocks = re.findall(block_pattern, markdown, re.DOTALL)
        assert len(blocks) > 0, "Block math not properly formatted"

    def test_no_empty_equations(self, math_docx_path: Path) -> None:
        """Verify no empty equation blocks."""
        converter = WordToMarkdownConverter(math_docx_path)
        markdown = converter.convert()

        # Should not have empty $$ $$ blocks
        assert "$$\n$$" not in markdown, "Empty equation block found"
        assert "$$$$" not in markdown, "Empty inline equation found"


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_nonexistent_file(self, tmp_path: Path) -> None:
        """Test handling of non-existent file."""
        fake_path = tmp_path / "nonexistent.docx"
        converter = WordToMarkdownConverter(fake_path)

        with pytest.raises(FileNotFoundError):
            converter.convert()

    def test_invalid_file(self, tmp_path: Path) -> None:
        """Test handling of invalid docx file."""
        # Create a fake file that's not a valid docx
        fake_file = tmp_path / "fake.docx"
        fake_file.write_text("This is not a valid docx file")

        converter = WordToMarkdownConverter(fake_file)

        with pytest.raises(ValueError):
            converter.convert()

    def test_empty_conversion_result(self) -> None:
        """Test that empty results are handled gracefully."""
        # This tests the internal handling, not actual conversion
        pass  # Placeholder for potential future edge case


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
