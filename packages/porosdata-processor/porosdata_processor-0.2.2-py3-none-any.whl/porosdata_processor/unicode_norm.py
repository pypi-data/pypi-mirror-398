# -*- coding: utf-8 -*-
"""
Unicode 归一化插件 - LLM 训练语料预处理优化

此插件专为大规模语言模型训练设计，实现Unicode文本的标准化和噪声消除，
提升训练数据的质量和Token效率。

核心功能：
- NFKC 归一化：统一Unicode字符的表示形式
- 噪声消除：移除零宽字符、控制字符等干扰因子
- 符号标准化：统一引号、括号等符号的表示

对LLM训练的优化意义：
- 减少Token碎片化，提升词汇表利用率
- 消除编码噪声，改善模型训练稳定性
- 标准化输入格式，提升模型泛化能力
"""

import re
import unicodedata
from typing import Dict, List, Set

from .plugin_system import PluginRegistry


class UnicodeNormalizer:
    """
    Unicode 归一化和噪声消除处理器

    专为LLM训练优化的Unicode处理引擎，支持多种归一化策略
    和噪声消除选项。
    """

    def __init__(
        self,
        normalization_form: str = 'NFKC',
        remove_invisible: bool = True,
        remove_zero_width: bool = True,
        standardize_quotes: bool = True,
        standardize_brackets: bool = False,
        remove_control_chars: bool = True
    ):
        """
        初始化Unicode归一化器

        Args:
            normalization_form: Unicode归一化形式 ('NFC', 'NFKC', 'NFD', 'NFKD')
            remove_invisible: 是否移除不可见字符 (零宽空格等)
            remove_zero_width: 是否移除零宽度字符
            standardize_quotes: 是否标准化引号 (统一为标准引号)
            standardize_brackets: 是否标准化括号
            remove_control_chars: 是否移除控制字符
        """
        self.normalization_form = normalization_form
        self.remove_invisible = remove_invisible
        self.remove_zero_width = remove_zero_width
        self.standardize_quotes = standardize_quotes
        self.standardize_brackets = standardize_brackets
        self.remove_control_chars = remove_control_chars

        # 预编译正则表达式以提高性能
        self._compile_patterns()

    def _compile_patterns(self):
        """预编译正则表达式模式"""

        # 不可见字符模式 (不包括换行符和制表符)
        if self.remove_invisible:
            self.invisible_pattern = re.compile(
                r'[\u200B-\u200F\u202A-\u202E\uFEFF\uFFF9-\uFFFB]'
            )

        # 零宽度字符模式
        if self.remove_zero_width:
            self.zero_width_pattern = re.compile(
                r'[\u200B\u200C\u200D\u200E\u200F\uFEFF]'
            )

        # 控制字符模式 (排除常见的换行和制表)
        if self.remove_control_chars:
            self.control_pattern = re.compile(
                r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]'
            )

    def normalize(self, text: str) -> str:
        """
        执行完整的Unicode归一化和噪声消除

        处理流程：
        1. Unicode归一化
        2. 移除不可见字符
        3. 移除零宽度字符
        4. 标准化引号
        5. 标准化括号 (可选)
        6. 移除控制字符

        Args:
            text: 输入文本

        Returns:
            归一化后的文本
        """
        # 1. Unicode归一化 - 统一字符表示形式
        text = unicodedata.normalize(self.normalization_form, text)

        # 2. 移除不可见字符
        if self.remove_invisible:
            text = self.invisible_pattern.sub('', text)

        # 3. 移除零宽度字符 (更严格的清理)
        if self.remove_zero_width:
            text = self.zero_width_pattern.sub('', text)

        # 4. 移除控制字符
        if self.remove_control_chars:
            text = self.control_pattern.sub('', text)

        # 5. 标准化引号
        if self.standardize_quotes:
            text = self._standardize_quotes(text)

        # 6. 标准化括号 (可选)
        if self.standardize_brackets:
            text = self._standardize_brackets(text)

        return text

    def _standardize_quotes(self, text: str) -> str:
        """
        标准化引号字符

        将各种类型的引号统一为标准形式：
        - 双引号：", ", ", ", " → "
        - 单引号：', ', ', ', ' → '
        """
        # 标准化双引号
        text = text.replace('"', '"')  # 左双引号
        text = text.replace('"', '"')  # 右双引号
        text = text.replace('"', '"')  # 弯双引号
        text = text.replace('"', '"')  # 低位双引号

        # 标准化单引号
        text = text.replace(''', "'")  # 左单引号
        text = text.replace(''', "'")  # 右单引号
        text = text.replace(''', "'")  # 弯单引号
        text = text.replace(''', "'")  # 低位单引号

        return text

    def _standardize_brackets(self, text: str) -> str:
        """
        标准化括号字符 (可选功能)

        统一中英文括号的表示形式
        """
        # 中文全角括号转换为英文半角
        bracket_map = {
            '（': '(', '）': ')',
            '【': '[', '】': ']',
            '《': '<', '》': '>',
            '「': '"', '」': '"',
            '『': '"', '』': '"'
        }

        for full_width, half_width in bracket_map.items():
            text = text.replace(full_width, half_width)

        return text

    def analyze_text(self, text: str) -> Dict:
        """
        分析文本中的Unicode特征

        用于调试和优化，提供文本特征统计

        Args:
            text: 输入文本

        Returns:
            包含各种Unicode特征统计的字典
        """
        analysis = {
            'total_chars': len(text),
            'unique_chars': len(set(text)),
            'invisible_chars': 0,
            'zero_width_chars': 0,
            'control_chars': 0,
            'normalized_forms': {},
            'character_categories': {}
        }

        # 统计各种字符类型
        for char in text:
            category = unicodedata.category(char)
            if category not in analysis['character_categories']:
                analysis['character_categories'][category] = 0
            analysis['character_categories'][category] += 1

            # 检查是否为不可见字符
            if char in '\u200B\u200C\u200D\u200E\u200F\uFEFF':
                analysis['zero_width_chars'] += 1
            elif unicodedata.category(char) in ['Cf', 'Cc'] and char not in '\n\t':
                analysis['invisible_chars'] += 1
                if ord(char) < 32 or (127 <= ord(char) <= 159):
                    analysis['control_chars'] += 1

        return analysis

    def get_supported_forms(self) -> List[str]:
        """获取支持的Unicode归一化形式"""
        return ['NFC', 'NFKC', 'NFD', 'NFKD']


# 插件注册 - Unicode归一化插件
@PluginRegistry.register("unicode_normalization")
def apply_unicode_normalization(text: str) -> str:
    """
    Unicode归一化插件 - 为LLM训练优化的文本预处理

    此插件执行以下操作：
    1. NFKC归一化 - 统一字符表示，提升Token效率
    2. 移除零宽字符 - 消除训练噪声
    3. 标准化引号 - 统一符号表示
    4. 移除控制字符 - 提升文本清洁度

    对LLM训练的意义：
    - 减少Token碎片化 (NFKC压缩复合字符)
    - 消除不可见噪声 (零宽字符干扰训练)
    - 提升模型稳定性 (标准化输入格式)
    - 优化推理性能 (更少的Token计算开销)

    Args:
        text: 输入文本 (可能包含占位符)

    Returns:
        Unicode归一化后的文本
    """
    normalizer = UnicodeNormalizer(
        normalization_form='NFKC',    # 兼容性组合，适合大多数场景
        remove_invisible=True,        # 移除不可见字符
        remove_zero_width=True,       # 移除零宽度字符
        standardize_quotes=True,      # 标准化引号
        standardize_brackets=False,   # 保持原有括号格式
        remove_control_chars=True     # 移除控制字符
    )

    return normalizer.normalize(text)

