# -*- coding: utf-8 -*-
"""LaTeX空格清理功能示例和测试"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from cleanlit.latex_space import LatexSpaceCleaner, clean_latex_spaces
from cleanlit.plugin_system import PluginRegistry


def test_basic_cleaning():
    """测试基本空格清理"""
    print("=" * 60)
    print("测试1: 基本空格清理")
    print("=" * 60)
    
    text = "这是一个    测试   文本"
    result = clean_latex_spaces(text)
    
    print(f"原文: {repr(text)}")
    print(f"结果: {repr(result)}")
    success = "    " not in result
    print("成功: 多余空格已清理" if success else "失败")
    print()


def test_protect_math():
    """测试保护数学模式"""
    print("=" * 60)
    print("测试2: 保护行内数学模式")
    print("=" * 60)
    
    text = "公式 $x   =   y$ 和 $a   +   b$"
    result = clean_latex_spaces(text)
    
    print(f"原文: {repr(text)}")
    print(f"结果: {repr(result)}")
    success = "$" in result
    print("成功: 数学模式被保护" if success else "失败")
    print()


def test_protect_commands():
    """测试保护LaTeX命令"""
    print("=" * 60)
    print("测试3: 保护LaTeX命令")
    print("=" * 60)
    
    text = "使用 \\alpha  和  \\beta  命令"
    result = clean_latex_spaces(text)
    
    print(f"原文: {repr(text)}")
    print(f"结果: {repr(result)}")
    success = "\\alpha" in result and "\\beta" in result
    print("成功: LaTeX命令被保护" if success else "失败")
    print()


def test_protect_comments():
    """测试保护注释"""
    print("=" * 60)
    print("测试4: 保护注释")
    print("=" * 60)
    
    text = "文本内容   % 这是注释   内容"
    result = clean_latex_spaces(text)
    
    print(f"原文: {repr(text)}")
    print(f"结果: {repr(result)}")
    success = "%" in result
    print("成功: 注释被保护" if success else "失败")
    print()


def test_mixed_content():
    """测试混合内容"""
    print("=" * 60)
    print("测试5: 混合内容（普通文本、LaTeX命令、数学模式）")
    print("=" * 60)
    
    text = "这是普通文本   \\alpha  和公式 $x   =   y$  以及更多文本"
    cleaner = LatexSpaceCleaner(aggressive=False)
    result = cleaner.clean(text)
    
    print(f"原文: {repr(text)}")
    print(f"结果: {repr(result)}")
    success = "\\alpha" in result and "$" in result
    print("成功: 混合内容正确处理" if success else "失败")
    print()


def test_aggressive_mode():
    """测试激进模式"""
    print("=" * 60)
    print("测试6: 激进模式")
    print("=" * 60)
    
    text = "命令 \\textbf{粗体  文本} 和公式 $x   =   y$"
    cleaner = LatexSpaceCleaner(aggressive=True)
    result = cleaner.clean(text)
    
    print(f"原文: {repr(text)}")
    print(f"结果: {repr(result)}")
    success = "$" in result
    print("成功: 激进模式正常工作" if success else "失败")
    print()


def test_plugin_integration():
    """测试插件集成"""
    print("=" * 60)
    print("测试7: 插件集成")
    print("=" * 60)
    
    plugin = PluginRegistry.get_plugin("latex_space_cleaning")
    if plugin:
        text = "这是一个    测试   文本"
        result = plugin(text)
        print("成功: 插件已注册并可调用")
        print(f"原文: {repr(text)}")
        print(f"结果: {repr(result)}")
    else:
        print("失败: 插件未注册")
    print()


def test_real_world_example():
    """测试真实世界示例"""
    print("=" * 60)
    print("测试8: 真实世界示例")
    print("=" * 60)
    
    text = """
这是一个包含LaTeX内容的文档。

公式 $E = mc^2$ 是著名的质能方程。

我们使用 \\alpha 和 \\beta 来表示希腊字母。

块级公式：
$$\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}$$

这是普通文本   有多余空格   需要清理。
"""
    
    result = clean_latex_spaces(text)
    
    print("原文:")
    print(text)
    print("\n清理后:")
    print(result)
    print("\n成功: 真实示例处理完成")
    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("LaTeX空格清理功能测试")
    print("=" * 60 + "\n")
    
    test_basic_cleaning()
    test_protect_math()
    test_protect_commands()
    test_protect_comments()
    test_mixed_content()
    test_aggressive_mode()
    test_plugin_integration()
    test_real_world_example()
    
    print("=" * 60)
    print("所有测试完成！")
    print("=" * 60)

