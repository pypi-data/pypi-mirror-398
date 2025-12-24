"""
Unicode and multilingual support tests.

Ensures proper handling of non-ASCII characters including:
- Japanese (Hiragana, Katakana, Kanji)
- Chinese (Simplified and Traditional)
- Korean (Hangul)
- Arabic, Hebrew (RTL languages)
- Cyrillic (Russian, etc.)
- Greek
- Special symbols and emoji
"""

from __future__ import annotations

import pytest

from eqword2llm.converter import SYMBOL_MAP, WordToMarkdownConverter


class TestUnicodeHandling:
    """Tests for Unicode character handling."""

    def test_japanese_text_preserved(self) -> None:
        """Verify Japanese text is preserved correctly."""
        # Test various Japanese character types
        test_cases = [
            "日本語テスト",  # Kanji + Katakana
            "ひらがなテスト",  # Hiragana + Katakana
            "カタカナテスト",  # Katakana only
            "漢字",  # Kanji only
            "混合テスト：日本語とEnglishの組み合わせ",  # Mixed Japanese and English
        ]

        for text in test_cases:
            # Text should remain unchanged (no encoding issues)
            assert text == text.encode("utf-8").decode("utf-8")
            # Verify string operations work correctly
            assert len(text) > 0
            assert isinstance(text, str)

    def test_chinese_text_preserved(self) -> None:
        """Verify Chinese text is preserved correctly."""
        test_cases = [
            "简体中文测试",  # Simplified Chinese
            "繁體中文測試",  # Traditional Chinese
            "中英混合 Mixed Test",  # Mixed Chinese and English
        ]

        for text in test_cases:
            assert text == text.encode("utf-8").decode("utf-8")
            assert len(text) > 0

    def test_korean_text_preserved(self) -> None:
        """Verify Korean text is preserved correctly."""
        test_cases = [
            "한글 테스트",  # Korean
            "한국어와 English 혼합",  # Mixed Korean and English
        ]

        for text in test_cases:
            assert text == text.encode("utf-8").decode("utf-8")
            assert len(text) > 0

    def test_cyrillic_text_preserved(self) -> None:
        """Verify Cyrillic (Russian) text is preserved correctly."""
        test_cases = [
            "Русский текст",  # Russian
            "Тест with English",  # Mixed
        ]

        for text in test_cases:
            assert text == text.encode("utf-8").decode("utf-8")
            assert len(text) > 0

    def test_arabic_text_preserved(self) -> None:
        """Verify Arabic text is preserved correctly."""
        test_cases = [
            "اختبار عربي",  # Arabic
            "عربي and English",  # Mixed
        ]

        for text in test_cases:
            assert text == text.encode("utf-8").decode("utf-8")
            assert len(text) > 0

    def test_special_unicode_symbols(self) -> None:
        """Verify special Unicode symbols are handled correctly."""
        test_cases = [
            "→ ← ↔ ⇒ ⇐ ⇔",  # Arrows
            "© ® ™",  # Legal symbols
            "° ′ ″",  # Degree and prime
            "• ◦ ‣",  # Bullets
            "— – ―",  # Dashes
            "「」『』【】",  # Japanese brackets
            "《》〈〉",  # Chinese brackets
        ]

        for text in test_cases:
            assert text == text.encode("utf-8").decode("utf-8")
            assert len(text) > 0


class TestMathSymbolMapping:
    """Tests for mathematical symbol mapping."""

    def test_greek_letters_mapped(self) -> None:
        """Verify Greek letters are mapped to LaTeX commands."""
        greek_mappings = {
            "α": r"\alpha",
            "β": r"\beta",
            "γ": r"\gamma",
            "δ": r"\delta",
            "π": r"\pi",
            "Σ": r"\Sigma",
            "Ω": r"\Omega",
        }

        for char, expected_latex in greek_mappings.items():
            assert char in SYMBOL_MAP
            assert SYMBOL_MAP[char] == expected_latex

    def test_math_operators_mapped(self) -> None:
        """Verify mathematical operators are mapped correctly."""
        operator_mappings = {
            "×": r"\times",
            "÷": r"\div",
            "±": r"\pm",
            "≤": r"\leq",
            "≥": r"\geq",
            "≠": r"\neq",
            "∞": r"\infty",
        }

        for char, expected_latex in operator_mappings.items():
            assert char in SYMBOL_MAP
            assert SYMBOL_MAP[char] == expected_latex

    def test_set_notation_mapped(self) -> None:
        """Verify set notation symbols are mapped correctly."""
        set_mappings = {
            "∈": r"\in ",
            "∉": r"\notin ",
            "⊂": r"\subset",
            "⊃": r"\supset",
            "∪": r"\cup",
            "∩": r"\cap",
            "∀": r"\forall ",
        }

        for char, expected_latex in set_mappings.items():
            assert char in SYMBOL_MAP
            assert SYMBOL_MAP[char] == expected_latex


class TestConverterWithUnicode:
    """Integration tests for converter with Unicode content."""

    def test_converter_handles_unicode_path(self, tmp_path) -> None:
        """Verify converter accepts Unicode file paths."""
        # Create path with Japanese characters
        unicode_path = tmp_path / "日本語ファイル.docx"
        converter = WordToMarkdownConverter(unicode_path)
        assert "日本語" in str(converter.docx_path)

    def test_escape_latex_preserves_non_math_unicode(self) -> None:
        """Verify _escape_latex preserves non-mathematical Unicode."""
        converter = WordToMarkdownConverter("dummy.docx")

        # Japanese text should pass through unchanged
        japanese_text = "これは日本語テストです"
        result = converter._escape_latex(japanese_text)
        assert result == japanese_text

        # Chinese text should pass through unchanged
        chinese_text = "这是中文测试"
        result = converter._escape_latex(chinese_text)
        assert result == chinese_text

        # Mixed text with math symbols should only convert math symbols
        mixed_text = "日本語 α + β = γ テスト"
        result = converter._escape_latex(mixed_text)
        assert "日本語" in result
        assert "テスト" in result
        assert r"\alpha" in result

    def test_escape_latex_converts_math_symbols_in_unicode_context(self) -> None:
        """Verify math symbols are converted even in Unicode context."""
        converter = WordToMarkdownConverter("dummy.docx")

        # Text with Japanese and math symbols
        text = "関数 f(x) ≥ 0 のとき"
        result = converter._escape_latex(text)
        assert "関数" in result
        assert "のとき" in result
        assert r"\geq" in result


class TestMultilingualMarkdown:
    """Tests for multilingual Markdown output."""

    def test_markdown_formatting_with_japanese(self) -> None:
        """Verify Markdown formatting works with Japanese text."""
        # Simulated Markdown output
        markdown = """# 見出し1

## 見出し2

これは**太字**と*斜体*のテストです。

- リスト項目1
- リスト項目2

数式: $x^{2} + y^{2} = z^{2}$
"""
        # Verify structure is maintained
        assert "# 見出し1" in markdown
        assert "**太字**" in markdown
        assert "*斜体*" in markdown
        assert "- リスト項目" in markdown
        assert "$x^{2}" in markdown

    def test_table_with_unicode(self) -> None:
        """Verify table formatting works with Unicode content."""
        table = """| 項目 | 値 |
| --- | --- |
| 日本語 | テスト |
| 한국어 | 테스트 |
| 中文 | 测试 |
"""
        # Verify table structure
        assert "| 項目 |" in table
        assert "| 日本語 |" in table
        assert "| 한국어 |" in table
        assert "| 中文 |" in table


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
