# -*- coding: utf-8 -*-
"""希腊字母与 LaTeX 命令双向转换模块

本模块专注于：
- 将 Unicode 希腊字母转换为 LaTeX 命令（例如：α → \\alpha）
- 将 LaTeX 命令转换回 Unicode 希腊字母（例如：\\alpha → α）
"""

from typing import Dict
from .plugin_system import PluginRegistry

# 希腊字母到LaTeX命令的映射
GREEK_TO_LATEX: Dict[str, str] = {
    # 小写希腊字母
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
    # 大写希腊字母
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
    """希腊字母与 LaTeX 命令双向转换器"""
    
    def __init__(self):
        self.greek_to_latex = GREEK_TO_LATEX.copy()
        self.latex_to_greek = LATEX_TO_GREEK.copy()
    
    def to_latex(self, text: str) -> str:
        """将文本中的 Unicode 希腊字母转换为 LaTeX 命令"""
        result = text
        for greek_char, latex_cmd in self.greek_to_latex.items():
            result = result.replace(greek_char, latex_cmd)
        return result
    
    def from_latex(self, text: str) -> str:
        """将 LaTeX 命令转换为 Unicode 希腊字母"""
        result = text
        # 按长度排序，先匹配长的命令（如 \varepsilon）
        sorted_commands = sorted(
            self.latex_to_greek.items(),
            key=lambda x: len(x[0]),
            reverse=True,
        )
        for latex_cmd, greek_char in sorted_commands:
            result = result.replace(latex_cmd, greek_char)
        return result
    
    def convert(self, text: str, to_latex: bool = True) -> str:
        """根据方向参数执行转换"""
        if to_latex:
            return self.to_latex(text)
        return self.from_latex(text)


@PluginRegistry.register("greek_to_latex")
def convert_greek_to_latex(text: str) -> str:
    """便捷函数：将 Unicode 希腊字母转换为 LaTeX 命令（供 pipeline 使用）"""
    converter = GreekLatexConverter()
    return converter.to_latex(text)


def convert_latex_to_greek(text: str) -> str:
    """便捷函数：将 LaTeX 命令转换为 Unicode 希腊字母"""
    converter = GreekLatexConverter()
    return converter.from_latex(text)


