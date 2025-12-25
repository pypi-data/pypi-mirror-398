# -*- coding: utf-8 -*-
"""cleanlit 基本使用示例"""

from cleanlit import (
    TextCleaner,
    GreekLatexConverter,
    PatternCollection,
    DocumentNumberingRuleEngine,
)


def example_basic_cleaning():
    """基本清洗示例"""
    print("=== 基本清洗示例 ===")
    
    cleaner = TextCleaner()
    text = "这是一个  测试文本。包含α粒子、β射线。"
    
    cleaned = cleaner.clean(text)
    print(f"原始文本: {text}")
    print(f"清洗后: {cleaned}")
    print()


def example_greek_conversion():
    """希腊字母转换示例"""
    print("=== 希腊字母转换示例 ===")
    
    converter = GreekLatexConverter()
    
    # 转换为LaTeX
    text = "α粒子、β射线、γ辐射"
    latex = converter.to_latex(text)
    print(f"原始: {text}")
    print(f"LaTeX: {latex}")
    
    # 从LaTeX转换回希腊字母
    latex_text = r"\alpha粒子、\beta射线"
    greek = converter.from_latex(latex_text)
    print(f"LaTeX: {latex_text}")
    print(f"希腊字母: {greek}")
    print()


def example_patterns():
    """正则模式示例"""
    print("=== 正则模式示例 ===")
    
    patterns = PatternCollection()
    
    text = "这  是一个   测试\n\n\n多个换行"
    print(f"原始文本: {repr(text)}")
    
    # 应用单个模式
    result = patterns.apply_pattern(text, "extra_whitespace")
    print(f"应用空白模式后: {repr(result)}")
    
    # 应用所有模式
    result = patterns.apply_all(text)
    print(f"应用所有模式后: {repr(result)}")
    print()


def example_rules():
    """文档编号规则引擎示例"""
    print("=== 规则引擎示例 ===")
    
    rules = DocumentNumberingRuleEngine()
    
    text = "第I章 第一章 ①第一项"
    print(f"原始文本: {text}")
    
    result = rules.apply(text)
    print(f"应用规则后: {result}")
    print()


def example_file_cleaning():
    """文件清洗示例"""
    print("=== 文件清洗示例 ===")
    
    cleaner = TextCleaner()
    
    # 注意：这里需要实际的文件路径
    # cleaner.clean_file("input.txt", "output.txt")
    print("使用 cleaner.clean_file('input.txt', 'output.txt') 清洗文件")
    print()


if __name__ == "__main__":
    example_basic_cleaning()
    example_greek_conversion()
    example_patterns()
    example_rules()
    example_file_cleaning()

