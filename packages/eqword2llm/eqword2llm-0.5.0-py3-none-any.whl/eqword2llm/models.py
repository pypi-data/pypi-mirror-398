"""
Data models for eqword2llm.

Contains dataclasses for equation info, document metadata,
and conversion results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


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
