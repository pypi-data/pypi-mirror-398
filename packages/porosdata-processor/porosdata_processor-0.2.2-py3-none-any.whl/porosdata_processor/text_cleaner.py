# -*- coding: utf-8 -*-
"""文本清洗管线与插件编排模块

本模块提供 `TextCleaner` 类作为统一入口：
- 通过插件化 pipeline（patterns_cleaning, document_numbering_rules, greek_to_latex 等）组合清洗步骤
- 通过文本级插件（normalize_whitespace, remove_extra_spaces, latex_math_space_cleaning）处理空白与 LaTeX 数学空格
"""

from typing import Optional, Dict, Any, List
import logging
import re

from .plugin_system import PluginRegistry
from .config import DEFAULT_CLEAN_OPTIONS

# 导入模块以确保默认插件被注册（这些模块内部会向 PluginRegistry 注册插件）
from . import patterns  # 正则模式清洗（patterns_cleaning）
from . import document_numbering_rules  # 文档结构与编号规范化（document_numbering_rules）
from . import greek_latex_converter     # 希腊字母到 LaTeX 的转换（greek_to_latex）
from . import citation_rules           # 参考文献标号规范化（citation_rules）


class TextCleaner:
    """文本清洗管线主类（原 Cleaner，命名更精确以强调“文本清洗管线”角色）"""
    
    def __init__(
        self,
        pipeline: Optional[List[str]] = None,
        clean_options: Optional[Dict[str, bool]] = None,
    ):
        """
        初始化文本清洗管线

        Args:
            pipeline: 插件管线列表（按顺序执行）。
                     - 如果为 None，使用默认 pipeline: ["patterns_cleaning", "document_numbering_rules", "citation_rules", "greek_to_latex", "normalize_whitespace", "remove_extra_spaces"]
                     - 可用插件（完整列表）：
                       * "patterns_cleaning"              : 正则模式清洗（见 patterns.py）
                       * "document_numbering_rules"       : 文档结构与编号规范化（见 document_numbering_rules.py）
                       * "citation_rules"                 : 参考文献标号规范化（见 citation_rules.py）
                       * "greek_to_latex"                 : 希腊字母 → LaTeX 命令转换（见 greek_latex_converter.py）
                       * "normalize_whitespace"           : 文本空白规范化（固定在默认 pipeline 中）
                       * "remove_extra_spaces"            : 行内多余空格压缩（固定在默认 pipeline 中）
                       * "latex_math_space_cleaning"      : LaTeX 数学公式内部空格规范化（可选，需在 clean_options 中开启）
                     - 可以只选择部分插件，自定义处理流程
            clean_options: 高级清洗选项字典（布尔开关），用于在 pipeline 之外追加可选的高级处理。
                          注意：基础清洗功能已固定在默认 pipeline 中，不在此处配置。
        """
        self.clean_options = clean_options or DEFAULT_CLEAN_OPTIONS.copy()

        # 使用默认 pipeline 或用户指定的 pipeline
        if pipeline is None:
            # 默认 pipeline：包含所有基础清洗 + 核心转换 + 引用规范化
            # 注意：greek_to_latex 在 Shield 保护前单独执行，以确保公式内部字母也能转换
            self.pipeline = [
                "unicode_normalization",    # 🆕 新增：Unicode归一化 (首位，LLM优化)
                "patterns_cleaning",
                "citation_rules",           # 参考文献标号规范化（先处理，避免误伤）
                "document_numbering_rules",  # 文档结构编号
                "normalize_whitespace",      # 基础功能：空白规范化
                "remove_extra_spaces"        # 基础功能：多余空格压缩
            ]
        else:
            self.pipeline = pipeline
    
    def clean(self, text: str) -> str:
        """
        彻底清洗文本 - 解决公式内部清理盲区

        Pipeline 执行序列：
        1. 希腊字母转换 (pre-Shield) - 确保公式内外都能转换
        2. 公式空间塌陷 (pre-Shield) - Token极简化，压缩公式内部空格
        3. 预处理空格清理 (pre-Shield) - 清理公式外部空格
        4. Shield保护 - 锁定敏感内容
        5. Plugin Pipeline - 在占位符上执行清理
        6. Shield还原 - 恢复原始内容
        7. LaTeX公式内部清理 (强制) - 最终清理保障
        8. 最终空格清理 - 确保全局清洁

        Args:
            text: 输入文本

        Returns:
            清洗后的文本
        """
        # 0. 输入验证：处理空输入
        if text is None:
            return ""
        if not isinstance(text, str):
            raise TypeError(f"Input must be a string, got {type(text)}")
        if not text:
            return ""

        print(f"[DEBUG] Input text: {repr(text)}")  # 调试追踪

        # 1. 🏛️ 希腊字母转换 (PRE-SHIELD)
        # 确保所有希腊字母（包括公式内部）都能被转换
        from .greek_latex_converter import convert_greek_to_latex
        text = convert_greek_to_latex(text)
        print(f"[DEBUG] After Greek conversion: {repr(text)}")  # 调试追踪

        # 2. 🔧 公式空间塌陷 (PRE-SHIELD)
        # 高度压缩公式内部空格，实现Token极简化
        text = self._normalize_formula_spaces(text)
        print(f"[DEBUG] After formula space normalization: {repr(text)}")  # 调试追踪

        # 3. 🔧 预处理：清理公式外部的多余空格 (PRE-SHIELD)
        # 在Shield前进行初步空格清理，但不影响公式内容
        text = self._pre_shield_space_cleanup(text)
        print(f"[DEBUG] After pre-Shield cleanup: {repr(text)}")  # 调试追踪

        # 3. 🛡️ Shield保护：屏蔽代码块和公式
        protected_text, placeholders = self._apply_shield(text)
        print(f"[DEBUG] After Shield protection: {repr(protected_text)}")  # 调试追踪

        # 4. 🔄 Plugin Pipeline：在占位符上执行清理
        result = protected_text
        try:
            for plugin_name in self.pipeline:
                plugin = PluginRegistry.get_plugin(plugin_name)
                if plugin:
                    result = plugin(result)
                    print(f"[DEBUG] After {plugin_name}: {repr(result)}")  # 调试追踪
                else:
                    logging.warning(f"Plugin '{plugin_name}' not found in registry.")
        except Exception as e:
            logging.error(f"Error in pipeline execution for plugin '{plugin_name}': {e}")
            return text

        # 5. 🔄 Shield还原：恢复原始内容
        try:
            final_text = self._remove_shield(result, placeholders)
            print(f"[DEBUG] After Shield restoration: {repr(final_text)}")  # 调试追踪
        except Exception as e:
            logging.error(f"Error in shield removal: {e}")
            return text

        # 6. 🔧 LaTeX公式内部强制清理 (POST-SHIELD, 强制执行)
        # 解决"公式内部清理盲区"的核心问题
        try:
            final_text = clean_latex_math_spaces(final_text)
            print(f"[DEBUG] After LaTeX math space cleaning: {repr(final_text)}")  # 调试追踪
        except Exception as e:
            logging.error(f"Error in LaTeX math space cleaning: {e}")

        # 7. 🧹 最终全局空格清理 (FINAL CLEANUP)
        # 确保没有任何多余空格遗留
        final_text = self._final_global_space_cleanup(final_text)
        print(f"[DEBUG] After final cleanup: {repr(final_text)}")  # 调试追踪

        return final_text
    
    def clean_file(
        self, 
        input_path: str, 
        output_path: Optional[str] = None,
        encoding: str = "utf-8"
    ) -> str:
        """
        清洗文件
        
        支持所有文本文件格式，包括但不限于：
        - Markdown 文件 (.md)：清理其中的 LaTeX 公式空格
        - JSON 文件 (.json)：清理其中的文本字段中的 LaTeX 公式空格
        - 纯文本文件 (.txt)
        - LaTeX 源文件 (.tex, .latex)
        
        注意：此方法按文本方式处理文件，不解析文件结构（如 JSON 的键值对），
        只处理文本内容中的 LaTeX 数学公式（$...$ 和 $$...$$）。
        """
        from .utils import read_file, write_file
        
        # 读取文件
        content = read_file(input_path, encoding)
        
        # 清洗内容
        cleaned_content = self.clean(content)
        
        # 写入文件
        output = output_path or input_path
        write_file(output, cleaned_content, encoding)
        
        return cleaned_content
    
    def set_option(self, option: str, value: bool):
        """设置清洗选项"""
        self.clean_options[option] = value
    
    def get_option(self, option: str) -> bool:
        """获取清洗选项"""
        return self.clean_options.get(option, False)

    def _apply_shield(self, text: str) -> tuple[str, dict]:
        """
        保护敏感内容（代码块和数学公式），防止被清洗逻辑误伤

        使用正则表达式找到所有匹配项，将内容按顺序存入字典，
        返回替换占位符后的文本和占位符字典。

        Args:
            text: 输入文本

        Returns:
            (protected_text, placeholders): 保护后的文本和占位符字典
        """
        from .patterns import PatternCollection

        protected_text = text
        placeholders = {}
        placeholder_counter = 0

        # 获取保护模式
        patterns = PatternCollection().get_shield_patterns()

        for pattern_name, pattern in patterns:
            def replace_match(match):
                nonlocal placeholder_counter
                original_content = match.group(0)

                # 特殊处理：避免将货币符号误认为LaTeX公式
                if pattern_name == "latex_inline_math":
                    # 检查是否是货币符号（$后紧跟数字，且没有对应的闭合$）
                    content = match.group(0)
                    if re.match(r'^\$\d', content) and not content.endswith('$'):
                        # 这可能是货币符号，不保护
                        return content

                # 使用更安全的占位符格式，避免与普通文本冲突
                # 格式: __CLEANLIT_SHIELD_001__ （使用固定宽度数字，避免空格压缩影响）
                placeholder = f"__CLEANLIT_SHIELD_{placeholder_counter:03d}__"
                placeholders[placeholder] = original_content
                placeholder_counter += 1
                return placeholder

            protected_text = pattern.sub(replace_match, protected_text)

        return protected_text, placeholders

    def _normalize_formula_spaces(self, text: str) -> str:
        """
        公式空间塌陷 - Token极简化预处理

        在Shield保护前对公式进行高度压缩，实现LLM训练的Token极简化。
        只处理$...$公式，严格避免影响代码块。

        处理逻辑:
        1. 首尾空格清零: $ \alpha + \beta $ → $\alpha + \beta$
        2. 内部冗余压缩: 多余连续空格 → 单个空格
        3. 保持语义完整性: 不改变数学表达式结构
        """
        import re

        def _compress_formula_content(match):
            """压缩单个公式的内部内容"""
            formula_content = match.group(1)  # 获取$...$之间的内容

            # 1. 清理首尾空格（塌陷到$符号）
            formula_content = formula_content.strip()

            # 2. 压缩内部连续空格为单个空格
            formula_content = re.sub(r'[ \t]+', ' ', formula_content)

            return f"${formula_content}$"

        # 使用非贪婪匹配处理行内公式 $...$
        # 避免匹配跨行的$$...$$块级公式
        text = re.sub(r'\$([^$]*?)\$', _compress_formula_content, text)

        return text

    def _pre_shield_space_cleanup(self, text: str) -> str:
        """
        Shield保护前的预处理：清理公式外部的多余空格
        避免影响公式内容，但可以清理明显的外部空格问题
        """
        # 这里可以进行轻量级的外部空格清理
        # 主要避免极端情况，如连续的外部空格
        import re

        # 清理连续的换行符（保留双换行符）
        text = re.sub(r'\n{3,}', '\n\n', text)

        # 清理行首/行尾的连续空格（保留单个空格）
        text = re.sub(r'^[ \t]+', '', text, flags=re.MULTILINE)  # 行首连续空格
        text = re.sub(r'[ \t]+$', '', text, flags=re.MULTILINE)  # 行尾连续空格

        return text

    def _final_global_space_cleanup(self, text: str) -> str:
        """
        最终的全局空格清理：确保没有任何多余空格
        在所有处理完成后执行最后一次扫尾
        """
        import re

        # 清理连续空格（保留换行）
        text = re.sub(r'[ \t]+', ' ', text)

        # 清理行首行尾空格
        lines = text.split('\n')
        cleaned_lines = [line.strip() for line in lines]
        text = '\n'.join(cleaned_lines)

        # 清理连续空行（保留单个空行）
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text.strip()

    def _remove_shield(self, text: str, placeholders: dict) -> str:
        """
        将占位符还原为原始内容

        Args:
            text: 包含占位符的文本
            placeholders: 占位符字典

        Returns:
            还原后的文本
        """
        result = text
        for placeholder, original_content in placeholders.items():
            result = result.replace(placeholder, original_content)
        return result


# =========================
# 文本级格式清理插件实现区域
# =========================

@PluginRegistry.register("normalize_whitespace")
def normalize_whitespace(text: str) -> str:
    """
    规范化空白字符（文本级别的通用规则）

    - 将制表符转换为空格
    - 去除每行行尾多余空白
    - 保留行结构，不合并换行
    """
    # 将制表符转换为空格
    text = text.replace("\t", " ")
    # 规范化行尾空白
    lines = text.split("\n")
    lines = [line.rstrip() for line in lines]
    return "\n".join(lines)


@PluginRegistry.register("remove_extra_spaces")
def remove_extra_spaces(text: str) -> str:
    """
    移除多余空格（保留换行符结构）

    - 按行处理
    - 去除行首/行尾空格
    - 行内多个连续空格压缩为单个空格
    - 保护 Markdown 标题后的第一个空格（如 # Title 中的空格）
    """
    import re

    lines = text.split("\n")
    processed_lines = []
    for line in lines:
        # 移除行首行尾空格
        line = line.strip()

        # 保护和规范化 Markdown 标题
        # 匹配行首的 # ## ### 等标题标记（无论后面是否有空格）
        title_match = re.match(r'^(#{1,6})\s*(.*)', line)
        if title_match:
            # 如果是标题行，确保标题标记后有一个标准空格
            title_marker = title_match.group(1)
            title_content = title_match.group(2).strip()
            if title_content:
                # 规范化为空格分隔的标题格式
                line = f"{title_marker} {title_content}"
            else:
                # 只有标题标记的行，保持原样
                line = title_marker
        else:
            # 非标题行，正常处理多余空格
            line = " ".join(line.split())

        processed_lines.append(line)
    return "\n".join(processed_lines)


@PluginRegistry.register("latex_math_space_cleaning")
def clean_latex_math_spaces(text: str) -> str:
    """
    清理 LaTeX 数学公式内部的多余空格（主要针对 $...$ 和 $$...$$ 中的内容）

    此函数适用于所有包含 LaTeX 公式的文本格式，包括：
    - Markdown 文件中的行内公式和块级公式
    - JSON 文件文本字段中的 LaTeX 公式
    - 纯文本文件中的 LaTeX 公式
    - LaTeX 源文件中的数学环境

    设计目标：
    - 不改变公式语义，只做“格式上的收紧”
    - 典型修正：
      - '\\mathbf { X }' -> '\\mathbf{X}'
      - '\\mathrm { K }' -> '\\mathrm{K}'
      - '^ { 2 }' -> '^{2}'
      - '_ { 0 }' -> '_{0}'
    - 只在数学环境内部操作（$...$ / $$...$$），正文不动
    """

    # 行内公式：$...$（非贪婪匹配，避免跨越多段）
    inline_pattern = re.compile(r"\$(.+?)\$", re.DOTALL)

    # 块级公式：$$...$$
    display_pattern = re.compile(r"\$\$(.+?)\$\$", re.DOTALL)

    def _clean_segment(segment: str) -> str:
        """对单个数学环境内部的内容做局部空格清理"""
        s = segment

        # 1) 命令与花括号参数之间的空格：\command {arg} -> \command{arg}
        s = re.sub(r"\\([A-Za-z@]+)\s*\{", r"\\\1{", s)

        # 2) ^ / _ 与花括号之间的空格：^ { 2 } -> ^{ 2 }
        s = re.sub(r"\s*\^\s*\{", r"^{", s)
        s = re.sub(r"\s*_\s*\{", r"_{", s)

        # 3) 花括号内部首尾空格：{ X } -> {X}
        s = re.sub(r"\{\s*([^{}]+?)\s*\}", r"{\1}", s)

        # 4) 多个空格压缩为单个空格（只在数学模式内部）
        s = re.sub(r"[ \t]+", " ", s)

        return s

    # 先处理 $$...$$，再处理 $...$，避免交叉影响
    def _replace_display(m: re.Match) -> str:
        inner = m.group(1)
        return "$$" + _clean_segment(inner) + "$$"

    def _replace_inline(m: re.Match) -> str:
        inner = m.group(1)
        return "$" + _clean_segment(inner) + "$"

    text = display_pattern.sub(_replace_display, text)
    text = inline_pattern.sub(_replace_inline, text)
    return text


