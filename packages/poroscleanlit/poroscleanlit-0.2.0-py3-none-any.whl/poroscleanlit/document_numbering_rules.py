# -*- coding: utf-8 -*-
"""文档结构与编号规范化规则引擎

本模块专注于**文档结构相关的编号规范化**，包括：
- 章节号（第1章 / Chapter 1 等）
- 小节号（1.1、1.1.1 等）
- 罗马数字（I、II、III、iv 等）
- 圆圈数字索引（①、②、③ 等）

不处理：
- LaTeX 公式语法
- 希腊字母与 LaTeX 命令的转换（见 `greek_latex_converter.py`）
"""

import re
from typing import List, Callable, Optional
from .plugin_system import PluginRegistry


class DocumentNumberingRuleEngine:
    """文档结构与编号规范化规则引擎"""
    
    def __init__(self):
        self.rules: List[Callable[[str], str]] = []
        self._init_default_rules()
    
    def _init_default_rules(self):
        """初始化默认规则集合"""
        # 章节号规范化（第1章 / Chapter 1 等）
        self.add_rule(self._normalize_chapter_headings)
        # 节号规范化（1.1、1.1.1 等）
        self.add_rule(self._normalize_section_numbering)
        # 罗马数字规范化（I, II, III, iv 等 → 阿拉伯数字）
        self.add_rule(self._normalize_roman_numerals_to_arabic)
        # 圆圈数字索引规范化（①、②、③ 等 → 普通数字）
        self.add_rule(self._normalize_circled_index_numbers)
    
    def add_rule(self, rule_func: Callable[[str], str]):
        """添加清洗规则函数"""
        self.rules.append(rule_func)
    
    def remove_rule(self, rule_func: Callable[[str], str]):
        """移除规则函数"""
        if rule_func in self.rules:
            self.rules.remove(rule_func)
    
    def apply(self, text: str) -> str:
        """应用所有规则到文本"""
        result = text
        for rule in self.rules:
            result = rule(result)
        return result
    
    def _normalize_chapter_headings(self, text: str) -> str:
        """规范化章节号（如：第1章、第1节、Chapter 1 等）"""
        # 中文章节号：第X章、第X节
        text = re.sub(r'第([0-9]+)章', r'第\1章', text)
        text = re.sub(r'第([0-9]+)节', r'第\1节', text)
        
        # 英文章节号：Chapter X, Chapter X.
        text = re.sub(r'Chapter\s+([0-9]+)\s*\.', r'Chapter \1', text)
        text = re.sub(r'Chapter\s+([0-9]+)', r'Chapter \1', text)
        
        return text
    
    def _normalize_section_numbering(self, text: str) -> str:
        """规范化节号数字格式（如：1.1、1.1.1）

        注意：添加行首锚定，避免误伤正文中的日期和版本号
        """
        lines = text.split('\n')
        processed_lines = []

        for line in lines:
            # 只处理行首的节号格式，避免误伤正文中的 X.X.X
            # 匹配行首的节号（后跟标题内容）
            line = re.sub(r'^(\d+)\.(\d+)\.(\d+)\s+', r'\1.\2.\3 ', line)
            line = re.sub(r'^(\d+)\.(\d+)\s+', r'\1.\2 ', line)
            processed_lines.append(line)

        return '\n'.join(processed_lines)
    
    def _normalize_roman_numerals_to_arabic(self, text: str) -> str:
        """规范化独立罗马数字为阿拉伯数字（I, II, III → 1, 2, 3）

        注意：使用负向预查避免误伤方括号[]或圆括号()内的罗马数字（通常是参考文献标号）
        """
        # 罗马数字到阿拉伯数字的映射（1-20）
        roman_to_arabic = {
            'I': '1', 'II': '2', 'III': '3', 'IV': '4', 'V': '5',
            'VI': '6', 'VII': '7', 'VIII': '8', 'IX': '9', 'X': '10',
            'XI': '11', 'XII': '12', 'XIII': '13', 'XIV': '14', 'XV': '15',
            'XVI': '16', 'XVII': '17', 'XVIII': '18', 'XIX': '19', 'XX': '20'
        }

        # 小写罗马数字
        roman_to_arabic_lower = {k.lower(): v for k, v in roman_to_arabic.items()}
        roman_to_arabic.update(roman_to_arabic_lower)

        # 匹配独立的罗马数字（前后有单词边界，但排除[]()内的罗马数字）
        def replace_roman(match):
            roman = match.group(1)
            if roman in roman_to_arabic:
                return match.group(0).replace(roman, roman_to_arabic[roman])
            return match.group(0)

        # 排除被方括号包围的罗马数字（参考文献标号）
        # 方法：找到所有独立的罗马数字，但跳过那些被[]包围的

        # 策略变更：不转换任何被方括号包围的罗马数字，因为它们通常是参考文献标号
        # 只转换真正独立的罗马数字（前后都是非字母数字字符）

        def replace_roman(match):
            roman = match.group(1)
            # 检查这个罗马数字是否被方括号包围
            start = match.start()
            end = match.end()

            # 检查前面是否有左方括号，且后面有对应的右方括号
            bracket_start = text.rfind('[', 0, start)
            bracket_end = text.find(']', end, len(text))

            # 如果找到了匹配的方括号对，且罗马数字完全在方括号内，则不转换
            if (bracket_start != -1 and bracket_end != -1 and
                bracket_start < start and end <= bracket_end):
                return match.group(0)

            # 否则，正常转换（确保不引入额外空格）
            if roman in roman_to_arabic:
                return roman_to_arabic[roman]
            return roman

        pattern = r'\b([IVX]+)\b'
        text = re.sub(pattern, replace_roman, text)
        text = re.sub(pattern, replace_roman, text)
        return text
    
    def _normalize_circled_index_numbers(self, text: str) -> str:
        """规范化圆圈索引号（如：①、②、③ → 1, 2, 3）"""
        circled_numbers = {
            '①': '1', '②': '2', '③': '3', '④': '4', '⑤': '5',
            '⑥': '6', '⑦': '7', '⑧': '8', '⑨': '9', '⑩': '10',
            '⑪': '11', '⑫': '12', '⑬': '13', '⑭': '14', '⑮': '15',
            '⑯': '16', '⑰': '17', '⑱': '18', '⑲': '19', '⑳': '20'
        }
        
        for circled, normal in circled_numbers.items():
            text = text.replace(circled, normal)
        
        return text


def create_custom_numbering_rule(pattern: str, replacement: str) -> Callable[[str], str]:
    """
    创建自定义“文档编号规范化”规则函数
    
    Args:
        pattern: 正则表达式模式
        replacement: 替换字符串
        
    Returns:
        规则函数
    """
    compiled_pattern = re.compile(pattern)
    
    def rule(text: str) -> str:
        return compiled_pattern.sub(replacement, text)
    
    return rule


@PluginRegistry.register("document_numbering_rules")
def apply_document_numbering_rules(text: str) -> str:
    """应用所有文档编号规范化规则（可通过 pipeline 使用）"""
    engine = DocumentNumberingRuleEngine()
    return engine.apply(text)


