"""
pytest configuration and shared fixtures.
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def sample_latex_expressions() -> dict[str, str]:
    """Sample LaTeX expressions for testing."""
    return {
        "simple": r"x^{2} + y^{2} = z^{2}",
        "fraction": r"\frac{a}{b}",
        "sum": r"\sum_{i=1}^{n} x_i",
        "integral": r"\int_{0}^{\infty} e^{-x} dx",
        "sqrt": r"\sqrt{x^2 + y^2}",
        "greek": r"\alpha + \beta = \gamma",
        "forall": r"\forall x \in \mathbb{R}",
        "inequality": r"x \geq 0",
        "matrix": r"\begin{pmatrix} a & b \\ c & d \end{pmatrix}",
        "complex": r"\sum_{n=1}^{\infty} \frac{1}{n^2} = \frac{\pi^2}{6}",
    }


@pytest.fixture
def sample_markdown_with_math() -> str:
    """Sample Markdown with math expressions."""
    return """
# Test Document

## Inline Math

This is a test of $x^{2}$.

## Block Math

$$
\\frac{a}{b} + \\frac{c}{d}
$$

## Complex Math

$$
\\sum_{i=1}^{n} x_i = x_1 + x_2 + \\ldots + x_n
$$
"""
