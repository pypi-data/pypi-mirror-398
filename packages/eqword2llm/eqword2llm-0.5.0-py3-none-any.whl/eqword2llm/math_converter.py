"""
OMML to LaTeX converter for eqword2llm.

Contains the OmmlToLatexConverter class that handles conversion
of Office Math Markup Language (OMML) elements to LaTeX format.
"""

from __future__ import annotations

from xml.etree import ElementTree as ET

from .constants import NAMESPACES, SYMBOL_MAP


class OmmlToLatexConverter:
    """Converts OMML (Office Math Markup Language) elements to LaTeX."""

    def convert(self, element: ET.Element) -> str:
        """Convert OMML element to LaTeX string.

        Args:
            element: XML element containing OMML math content.

        Returns:
            LaTeX string representation of the math content.
        """
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
                result.append(self.convert(child))
            elif tag == "groupChr":
                result.append(self._convert_group_chr(child))
            elif tag == "borderBox":
                result.append(self.convert(child))
            else:
                nested = self.convert(child)
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

        num_latex = self.convert(num) if num is not None else ""
        den_latex = self.convert(den) if den is not None else ""

        # noBar type is typically used for binomial coefficients
        if frac_type == "noBar":
            return rf"\binom{{{num_latex}}}{{{den_latex}}}"

        return rf"\frac{{{num_latex}}}{{{den_latex}}}"

    def _convert_radical(self, rad: ET.Element) -> str:
        """Convert radical (square root)."""
        deg = rad.find("m:deg", NAMESPACES)
        e = rad.find("m:e", NAMESPACES)

        e_latex = self.convert(e) if e is not None else ""

        if deg is not None:
            deg_latex = self.convert(deg)
            if deg_latex and deg_latex.strip():
                return rf"\sqrt[{deg_latex}]{{{e_latex}}}"

        return rf"\sqrt{{{e_latex}}}"

    def _convert_superscript(self, ssup: ET.Element) -> str:
        """Convert superscript."""
        e = ssup.find("m:e", NAMESPACES)
        sup = ssup.find("m:sup", NAMESPACES)

        e_latex = self.convert(e) if e is not None else ""
        sup_latex = self.convert(sup) if sup is not None else ""

        if len(e_latex) > 1 and not (e_latex.startswith("{") and e_latex.endswith("}")):
            e_latex = f"{{{e_latex}}}"

        return f"{e_latex}^{{{sup_latex}}}"

    def _convert_subscript(self, ssub: ET.Element) -> str:
        """Convert subscript."""
        e = ssub.find("m:e", NAMESPACES)
        sub = ssub.find("m:sub", NAMESPACES)

        e_latex = self.convert(e) if e is not None else ""
        sub_latex = self.convert(sub) if sub is not None else ""

        if len(e_latex) > 1 and not (e_latex.startswith("{") and e_latex.endswith("}")):
            e_latex = f"{{{e_latex}}}"

        return f"{e_latex}_{{{sub_latex}}}"

    def _convert_subsup(self, ssubsup: ET.Element) -> str:
        """Convert subscript-superscript."""
        e = ssubsup.find("m:e", NAMESPACES)
        sub = ssubsup.find("m:sub", NAMESPACES)
        sup = ssubsup.find("m:sup", NAMESPACES)

        e_latex = self.convert(e) if e is not None else ""
        sub_latex = self.convert(sub) if sub is not None else ""
        sup_latex = self.convert(sup) if sup is not None else ""

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

        sub_latex = self.convert(sub) if sub is not None else ""
        sup_latex = self.convert(sup) if sup is not None else ""
        e_latex = self.convert(e) if e is not None else ""

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
            content_parts.append(self.convert(e))

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
                cols.append(self.convert(e))
            rows.append(" & ".join(cols))
        return r" \\ ".join(rows)

    def _convert_function(self, func: ET.Element) -> str:
        """Convert function."""
        fName = func.find("m:fName", NAMESPACES)
        e = func.find("m:e", NAMESPACES)

        func_name = self.convert(fName) if fName is not None else ""
        e_latex = self.convert(e) if e is not None else ""

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
            rows.append(self.convert(e))

        if len(rows) > 1:
            return r"\begin{aligned}" + r" \\ ".join(rows) + r"\end{aligned}"
        return rows[0] if rows else ""

    def _convert_matrix(self, matrix: ET.Element) -> str:
        """Convert matrix."""
        rows: list[str] = []
        for mr in matrix.findall("m:mr", NAMESPACES):
            cols: list[str] = []
            for e in mr.findall("m:e", NAMESPACES):
                cols.append(self.convert(e))
            rows.append(" & ".join(cols))

        return r"\begin{pmatrix}" + r" \\ ".join(rows) + r"\end{pmatrix}"

    def _convert_lim_low(self, lim_low: ET.Element) -> str:
        """Convert lower limit."""
        e = lim_low.find("m:e", NAMESPACES)
        lim = lim_low.find("m:lim", NAMESPACES)

        e_latex = self.convert(e) if e is not None else ""
        lim_latex = self.convert(lim) if lim is not None else ""

        return f"{e_latex}_{{{lim_latex}}}"

    def _convert_lim_upp(self, lim_upp: ET.Element) -> str:
        """Convert upper limit."""
        e = lim_upp.find("m:e", NAMESPACES)
        lim = lim_upp.find("m:lim", NAMESPACES)

        e_latex = self.convert(e) if e is not None else ""
        lim_latex = self.convert(lim) if lim is not None else ""

        return f"{e_latex}^{{{lim_latex}}}"

    def _convert_accent(self, acc: ET.Element) -> str:
        """Convert accent."""
        accPr = acc.find("m:accPr", NAMESPACES)
        e = acc.find("m:e", NAMESPACES)

        e_latex = self.convert(e) if e is not None else ""

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
        e_latex = self.convert(e) if e is not None else ""

        return rf"\overline{{{e_latex}}}"

    def _convert_group_chr(self, group_chr: ET.Element) -> str:
        """Convert group character."""
        e = group_chr.find("m:e", NAMESPACES)
        e_latex = self.convert(e) if e is not None else ""

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
