from .text_cleaner import TextCleaner
from .patterns import PatternCollection
from .document_numbering_rules import DocumentNumberingRuleEngine, create_custom_numbering_rule
from .greek_latex_converter import GreekLatexConverter

# 导入插件模块以确保注册 (这些模块内部会向 PluginRegistry 注册插件)
from . import unicode_norm  # Unicode归一化插件

__version__ = "0.2.2"
__all__ = [
    "TextCleaner",
    "PatternCollection",
    "DocumentNumberingRuleEngine",
    "create_custom_numbering_rule",
    "GreekLatexConverter",
]
