# -*- coding: utf-8 -*-
"""参考文献标号规范化规则

本模块专注于参考文献标号的标准化处理，包括：
- 全角括号转半角括号
- 内侧空格清理
- 外侧间距优化
- 保护罗马数字文献号

不处理：
- Markdown 链接语法 [text](url)
- 文档结构编号（见 document_numbering_rules.py）
"""

import re
from typing import List, Callable
from .plugin_system import PluginRegistry


class CitationRulesEngine:
    """参考文献标号规范化规则引擎"""

    def __init__(self):
        self.rules: List[Callable[[str], str]] = []
        self._init_default_rules()

    def _init_default_rules(self):
        """初始化默认规则集合"""
        # 全角括号转半角
        self.add_rule(self._normalize_fullwidth_brackets)
        # 内侧空格清理
        self.add_rule(self._normalize_inner_spaces)
        # 外侧间距优化
        self.add_rule(self._optimize_outer_spacing)

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

        # 最后恢复被保护的罗马数字文献号
        result = re.sub(r'__ROMAN_CITATION_([IVXLCDM]+)__', r'\1', result)

        return result

    def _normalize_fullwidth_brackets(self, text: str) -> str:
        """全角括号转半角括号"""
        # 【N】 → [N] (中文全角方括号)
        text = re.sub(r'【([^\[\]]*)】', r'[\1]', text)
        # ［N］ → [N] (全角方括号)
        text = re.sub(r'［([^\[\]]*)］', r'[\1]', text)
        # 〔N〕 → [N] (全角六角括号)
        text = re.sub(r'〔([^\[\]]*)〕', r'[\1]', text)

        return text

    def _normalize_inner_spaces(self, text: str) -> str:
        """清理参考文献标号内的多余空格

        例如：[ 12 ] → [12]，[ 1, 2 ] → [1,2]，[ I ] → [I]
        注意：会保护罗马数字文献号，防止被后续的罗马数字转换规则误伤
        """
        # 匹配方括号内的内容，清理内部空格
        def clean_inner(match):
            content = match.group(1)
            # 清理内容中的空格
            cleaned = re.sub(r'\s+', '', content)

            # 如果清理后的内容是纯罗马数字，则标记为保护状态
            # 使用特殊前缀避免被 document_numbering_rules 的罗马数字转换影响
            if re.match(r'^[IVXLCDM]+$', cleaned):
                return f'[__ROMAN_CITATION_{cleaned}__]'
            else:
                return f'[{cleaned}]'

        # 只匹配方括号内包含数字、罗马数字、逗号、短横线的组合
        # 避免匹配 Markdown 链接 [text](url)
        pattern = r'\[([IVXLCDM\d,\-\s]+)\]'
        text = re.sub(pattern, clean_inner, text)

        return text

    def _optimize_outer_spacing(self, text: str) -> str:
        """优化参考文献标号的外侧间距

        - 行内引用：移除标号前的不必要多余空格（文本  [1] → 文本[1]）
        - 行首列表：确保标号后跟一个标准空格（[1]作者名 → [1] 作者名）
        """
        lines = text.split('\n')
        processed_lines = []

        for line in lines:
            # 处理行内引用：移除标号前的一个或多个空格（但保留标点后的空格）
            # 只匹配字母/数字/中文字符后的空格+标号
            line = re.sub(r'([a-zA-Z0-9\u4e00-\u9fa5])\s{1,}(\[[IVXLCDM\d,\-]+\])', r'\1\2', line)

            # 处理行首列表：确保标号后有一个空格（如果后面是非空格字符）
            # 但避免在标号后已经有空格的情况下重复添加
            line = re.sub(r'^(\[[IVXLCDM\d,\-]+\])(?!\s)(\S)', r'\1 \2', line)

            processed_lines.append(line)

        return '\n'.join(processed_lines)


@PluginRegistry.register("citation_rules")
def apply_citation_rules(text: str) -> str:
    """应用所有参考文献标号规范化规则（可通过 pipeline 使用）"""
    engine = CitationRulesEngine()
    return engine.apply(text)
