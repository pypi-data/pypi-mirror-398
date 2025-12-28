# -*- coding: utf-8 -*-
"""正则表达式模式集合"""

import re
from typing import List, Pattern, Tuple, Union, Callable
from .plugin_system import PluginRegistry


class PatternCollection:
    """正则表达式模式集合类"""
    
    def __init__(self):
        self._patterns: List[Tuple[str, Pattern, Union[str, Callable]]] = []
        self._compile_patterns()
    
    def _compile_patterns(self):
        """编译所有正则表达式模式"""
        patterns = [
            # 多余空白字符（保留换行符，只处理空格和制表符）
            ("extra_whitespace", re.compile(r'[ \t]+'), ' '),
            
            # 行首行尾空白（保留换行符，只处理空格和制表符）
            ("line_whitespace", re.compile(r'^[ \t]+|[ \t]+$', re.MULTILINE), ''),
            
            # 多个连续换行（规范化：最多保留两个连续换行）
            ("multiple_newlines", re.compile(r'\n{3,}'), '\n\n'),
            
            # 中文和英文之间的空格（只匹配空格，不匹配换行符）
            ("chinese_english_space", re.compile(r'([\u4e00-\u9fa5])[ ]+([a-zA-Z])'), r'\1\2'),
            ("english_chinese_space", re.compile(r'([a-zA-Z])[ ]+([\u4e00-\u9fa5])'), r'\1\2'),
            
            # 标点符号前的空格（只匹配空格，不匹配换行符）
            ("space_before_punctuation", re.compile(r'[ ]+([，。！？；：、])'), r'\1'),
            
            # 引号规范化（中文引号）
            ("chinese_quotes", re.compile(r'[""]'), '"'),
            ("chinese_quotes_single", re.compile(r"['']"), "'"),
            
            # 省略号规范化
            ("ellipsis", re.compile(r'\.{3,}'), '...'),
            ("chinese_ellipsis", re.compile(r'…+'), '...'),
            
            # 破折号规范化
            ("em_dash", re.compile(r'—+'), '—'),
            ("en_dash", re.compile(r'–+'), '–'),
            
            # 全角字符转半角（数字和字母）
            ("fullwidth_numbers", re.compile(r'[０-９]'), lambda m: str(ord(m.group()) - 0xFEE0)),
            ("fullwidth_letters", re.compile(r'[Ａ-Ｚａ-ｚ]'), lambda m: chr(ord(m.group()) - 0xFEE0)),
        ]
        
        for name, pattern, replacement in patterns:
            self._patterns.append((name, pattern, replacement))
    
    def get_pattern(self, name: str) -> Tuple[Pattern, Union[str, Callable]]:
        """
        获取指定名称的模式
        
        Args:
            name: 模式名称
            
        Returns:
            (模式对象, 替换字符串或函数) 元组
        """
        for pattern_name, pattern, replacement in self._patterns:
            if pattern_name == name:
                return pattern, replacement
        raise ValueError(f"Pattern '{name}' not found")
    
    def apply_pattern(self, text: str, pattern_name: str) -> str:
        """
        应用指定模式到文本
        
        Args:
            text: 输入文本
            pattern_name: 模式名称
            
        Returns:
            处理后的文本
        """
        pattern, replacement = self.get_pattern(pattern_name)
        if callable(replacement):
            return pattern.sub(replacement, text)
        else:
            return pattern.sub(replacement, text)
    
    def apply_all(self, text: str, exclude: List[str] = None) -> str:
        """
        应用所有模式到文本
        
        Args:
            text: 输入文本
            exclude: 要排除的模式名称列表
            
        Returns:
            处理后的文本
        """
        exclude = exclude or []
        result = text
        for name, pattern, replacement in self._patterns:
            if name not in exclude:
                if callable(replacement):
                    result = pattern.sub(replacement, result)
                else:
                    result = pattern.sub(replacement, result)
        return result
    
    def list_patterns(self) -> List[str]:
        """列出所有可用的模式名称"""
        return [name for name, _, _ in self._patterns]

    def get_shield_patterns(self) -> List[Tuple[str, Pattern]]:
        """
        获取保护模式（用于屏蔽敏感内容，防止被清洗逻辑误伤）

        Returns:
            保护模式列表，每个元素为 (模式名称, 编译后的正则表达式) 元组
        """
        shield_patterns = [
            # Markdown 代码块保护（```...``` 或 ```language\n...\n```）
            ("markdown_code_block", re.compile(r'```(?:[^\n]*\n)?(?:.*?\n)*?```', re.DOTALL)),

            # 行内代码保护（`...`）
            ("inline_code", re.compile(r'`[^`\n]+`')),

            # LaTeX 行内数学公式（$...$）
            ("latex_inline_math", re.compile(r'\$[^$\n]+\$')),

            # LaTeX 展示数学公式（$$...$$ 或 \[...\] 或 \(...\)）
            ("latex_display_math", re.compile(r'\$\$[^$]*?\$\$|\\\[.*?\\\]|\\\(.*?\\\)')),

            # LaTeX 命令保护（\command{...} 或 \command[...] 或 \command）
            ("latex_commands", re.compile(r'\\[a-zA-Z]+\{[^}]*\}|\\[a-zA-Z]+\[[^\]]*\]|\\[a-zA-Z]+(?:\s|$)')),
        ]

        return shield_patterns


# 预定义的常用模式
COMMON_PATTERNS = PatternCollection()


@PluginRegistry.register("patterns_cleaning")
def apply_pattern_cleaning(text: str) -> str:
    """应用所有正则清洗模式"""
    return COMMON_PATTERNS.apply_all(text)
