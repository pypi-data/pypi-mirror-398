# -*- coding: utf-8 -*-
"""Greek Letter and LaTeX Command Bidirectional Conversion Module

This module focuses on:
- Converting Unicode Greek letters to LaTeX commands (e.g.: α → \\alpha)
- Converting LaTeX commands back to Unicode Greek letters (e.g.: \\alpha → α)
"""

from typing import Dict
from .plugin_system import PluginRegistry

# Greek letter to LaTeX command mapping
GREEK_TO_LATEX: Dict[str, str] = {
    # Lowercase Greek letters
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
    "ο": r"\omicron",
    "π": r"\pi",
    "ρ": r"\rho",
    "σ": r"\sigma",
    "τ": r"\tau",
    "υ": r"\upsilon",
    "φ": r"\phi",
    "χ": r"\chi",
    "ψ": r"\psi",
    "ω": r"\omega",
    # Uppercase Greek letters
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
    "Ο": r"\Omicron",
    "Π": r"\Pi",
    "Ρ": r"\Rho",
    "Σ": r"\Sigma",
    "Τ": r"\Tau",
    "Υ": r"\Upsilon",
    "Φ": r"\Phi",
    "Χ": r"\Chi",
    "Ψ": r"\Psi",
    "Ω": r"\Omega",
    # 变体（注意：这些是特殊的Unicode变体字符）
    "ϑ": r"\vartheta",   # 变体theta (U+03D1)
    "ς": r"\varsigma",  # 词尾sigma (U+03C2)
}

# LaTeX到希腊字母的反向映射（用于反向转换）
LATEX_TO_GREEK: Dict[str, str] = {v: k for k, v in GREEK_TO_LATEX.items()}


class GreekLatexConverter:
    """Greek Letter and LaTeX Command Bidirectional Converter"""
    
    def __init__(self):
        self.greek_to_latex = GREEK_TO_LATEX.copy()
        self.latex_to_greek = LATEX_TO_GREEK.copy()
    
    def to_latex(self, text: str) -> str:
        """Convert Unicode Greek letters in text to LaTeX commands"""
        result = text
        for greek_char, latex_cmd in self.greek_to_latex.items():
            result = result.replace(greek_char, latex_cmd)
        return result
    
    def from_latex(self, text: str) -> str:
        """Convert LaTeX commands to Unicode Greek letters"""
        result = text
        # Sort by length, match longer commands first (e.g. \varepsilon)
        sorted_commands = sorted(
            self.latex_to_greek.items(),
            key=lambda x: len(x[0]),
            reverse=True,
        )
        for latex_cmd, greek_char in sorted_commands:
            result = result.replace(latex_cmd, greek_char)
        return result
    
    def convert(self, text: str, to_latex: bool = True) -> str:
        """Execute conversion based on direction parameter"""
        if to_latex:
            return self.to_latex(text)
        return self.from_latex(text)


@PluginRegistry.register("greek_to_latex")
def convert_greek_to_latex(text: str) -> str:
    """Convenience function: Convert Unicode Greek letters to LaTeX commands (for pipeline use)"""
    converter = GreekLatexConverter()
    return converter.to_latex(text)


def convert_latex_to_greek(text: str) -> str:
    """Convenience function: Convert LaTeX commands to Unicode Greek letters"""
    converter = GreekLatexConverter()
    return converter.from_latex(text)


