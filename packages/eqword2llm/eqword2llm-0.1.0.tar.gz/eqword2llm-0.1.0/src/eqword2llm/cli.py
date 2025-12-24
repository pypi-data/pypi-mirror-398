"""
eqword2llm: Command Line Interface
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from eqword2llm.converter import WordToMarkdownConverter


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="eqword2llm",
        description="Convert equation-heavy Word documents (.docx) to Markdown for LLM. Math equations are converted to LaTeX format.",
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Path to the input Word document (.docx)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Path to the output Markdown file (stdout if omitted)",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="Show version",
    )

    args = parser.parse_args()

    if args.version:
        from eqword2llm import __version__

        print(f"eqword2llm {__version__}")
        return 0

    try:
        converter = WordToMarkdownConverter(args.input)
        markdown = converter.convert()

        if args.output:
            args.output.write_text(markdown, encoding="utf-8")
            print(f"Conversion complete: {args.output}", file=sys.stderr)
        else:
            print(markdown)

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
