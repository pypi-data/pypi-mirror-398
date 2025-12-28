# -*- coding: utf-8 -*-
"""测试 LaTeX 数学公式空格清理功能（支持 Markdown 和 JSON 文件）"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from cleanlit import TextCleaner


def test_markdown_file():
    """测试处理 Markdown 文件中的 LaTeX 公式"""
    print("=" * 60)
    print("测试1: Markdown 文件中的 LaTeX 公式清理")
    print("=" * 60)
    
    # 示例 Markdown 内容（包含需要清理的 LaTeX 公式）
    markdown_content = """# 测试文档

这是一个包含 LaTeX 公式的 Markdown 文档。

行内公式：$Z \\mathbf { r } -$ 和 $1 \\mathrm { n m }$ 

块级公式：
$$
\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}
$$

更多公式：$T _ { \\mathrm { g } }$ 和 $1 0 ^ { 2 } - 1 0 ^ { 0 } \\mathrm { K } / \\mathrm { s }$
"""
    
    cleaner = TextCleaner(
        clean_options={
            "clean_latex_math_spaces": True,  # 开启 LaTeX 数学公式空格清理
            "normalize_whitespace": False,    # 关闭其他清理，专注测试 LaTeX
            "remove_extra_spaces": False,
        }
    )
    
    result = cleaner.clean(markdown_content)
    
    print("原文（部分）:")
    print(markdown_content[:200] + "...")
    print("\n清理后（部分）:")
    print(result[:200] + "...")
    
    # 检查是否成功清理
    has_cleaned = "\\mathbf{" in result and "\\mathbf { r }" not in result
    print(f"\n结果: {'成功' if has_cleaned else '失败'}")
    print()


def test_json_content():
    """测试处理 JSON 文件中的 LaTeX 公式（文本字段）"""
    print("=" * 60)
    print("测试2: JSON 文件中的 LaTeX 公式清理")
    print("=" * 60)
    
    # 示例 JSON 内容（包含需要清理的 LaTeX 公式）
    json_content = '''{
  "text": "The thermal behavior of $Z \\mathbf { r } -$ and Pd-based bulk metallic glasses was studied by in situ $\\mathbf { X }$ -ray diffraction at elevated temperatures. The temperature dependence of the $\\mathbf { X }$ -ray structure factor of the glassy state can be well described by the Debye theory. At the caloric glass transition the temperature dependence of the structure alters, pointing to a continuous development of structural changes in the liquid state. The microstructure of metallic glasses consisting of elements with negative enthalpy of mixing is homogeneous at dimensions above $1 \\mathrm { n m }$ ."
}'''
    
    cleaner = TextCleaner(
        clean_options={
            "clean_latex_math_spaces": True,
            "normalize_whitespace": False,
            "remove_extra_spaces": False,
        }
    )
    
    result = cleaner.clean(json_content)
    
    print("原文（部分）:")
    print(json_content[:300] + "...")
    print("\n清理后（部分）:")
    print(result[:300] + "...")
    
    # 检查是否成功清理
    has_cleaned = "\\mathbf{" in result and "\\mathbf { r }" not in result
    print(f"\n结果: {'成功' if has_cleaned else '失败'}")
    print()


def test_mixed_content():
    """测试混合内容（Markdown + JSON 风格）"""
    print("=" * 60)
    print("测试3: 混合内容处理")
    print("=" * 60)
    
    mixed_content = """# 文档标题

这是普通文本，包含公式 $x   =   y$ 和 $a   +   b$。

JSON 格式的内容：
```json
{
  "formula": "$1 0 ^ { 2 } - 1 0 ^ { 0 } \\mathrm { K } / \\mathrm { s }$"
}
```

更多公式：$\\alpha   +   \\beta$ 和 $$\\int_{0}^{\\infty} e^{-x} dx = 1$$
"""
    
    cleaner = TextCleaner(
        clean_options={
            "clean_latex_math_spaces": True,
        }
    )
    
    result = cleaner.clean(mixed_content)
    
    print("原文:")
    print(mixed_content)
    print("\n清理后:")
    print(result)
    
    # 检查是否成功清理
    has_cleaned = "$x = y$" in result or "$x   =   y$" not in result
    print(f"\n结果: {'成功' if has_cleaned else '失败'}")
    print()


def test_file_processing():
    """测试实际文件处理（如果文件存在）"""
    print("=" * 60)
    print("测试4: 实际文件处理")
    print("=" * 60)
    
    # 检查是否存在测试文件
    md_file = Path("data/processed/cleaned/00001/mineru_2.1.10_output/00001/auto/00001.md")
    json_file = Path("data/mineru_output/00001/mineru_2.1.10_output/00001/auto/00001_content_list.json")
    
    cleaner = TextCleaner(
        clean_options={
            "clean_latex_math_spaces": True,
        }
    )
    
    if md_file.exists():
        print(f"处理 Markdown 文件: {md_file}")
        try:
            result = cleaner.clean_file(str(md_file), encoding="utf-8")
            print(f"成功: 已处理 {len(result)} 个字符")
            
            # 检查是否有清理效果
            with open(md_file, 'r', encoding='utf-8') as f:
                original = f.read()
            
            if "\\mathbf{" in result and "\\mathbf { r }" not in result:
                print("LaTeX 公式空格已清理")
            else:
                print("注意: 未检测到需要清理的 LaTeX 公式格式")
        except Exception as e:
            print(f"错误: {e}")
    else:
        print(f"文件不存在: {md_file}")
    
    if json_file.exists():
        print(f"\n处理 JSON 文件: {json_file}")
        try:
            # 注意：JSON 文件需要小心处理，因为可能会破坏 JSON 结构
            # 这里仅作演示，实际使用时建议先解析 JSON，只处理文本字段
            result = cleaner.clean_file(str(json_file), encoding="utf-8")
            print(f"成功: 已处理 {len(result)} 个字符")
            print("注意: JSON 文件处理可能会影响 JSON 结构，建议先解析再处理文本字段")
        except Exception as e:
            print(f"错误: {e}")
    else:
        print(f"文件不存在: {json_file}")
    
    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("LaTeX 数学公式空格清理功能测试（支持 Markdown 和 JSON）")
    print("=" * 60 + "\n")
    
    test_markdown_file()
    test_json_content()
    test_mixed_content()
    test_file_processing()
    
    print("=" * 60)
    print("所有测试完成！")
    print("=" * 60)
    print("\n使用说明:")
    print("1. 对于 Markdown 文件：直接使用 clean_file() 方法")
    print("2. 对于 JSON 文件：建议先解析 JSON，只处理文本字段中的 LaTeX 公式")
    print("3. 对于其他文本文件：直接使用 clean_file() 方法")
    print("\n示例代码:")
    print("""
from cleanlit import TextCleaner

# 处理 Markdown 文件
cleaner = TextCleaner(clean_options={"clean_latex_math_spaces": True})
cleaner.clean_file("input.md", "output.md")

# 处理 JSON 文件（建议方式）
import json
with open("input.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# 只处理文本字段
if "text" in data:
    data["text"] = cleaner.clean(data["text"])

with open("output.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
""")

