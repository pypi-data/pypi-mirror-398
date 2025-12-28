# -*- coding: utf-8 -*-
"""porosdata_processor basic usage examples"""

from porosdata_processor import (
    TextCleaner,
    GreekLatexConverter,
    PatternCollection,
    DocumentNumberingRuleEngine,
)


def example_basic_cleaning():
    """Basic cleaning example"""
    print("=== Basic Cleaning Example ===")

    cleaner = TextCleaner()
    text = "This is a  test text. Contains α particles, β rays."

    cleaned = cleaner.clean(text)
    print(f"Original text: {text}")
    print(f"After cleaning: {cleaned}")
    print()


def example_greek_conversion():
    """Greek letter conversion example"""
    print("=== Greek Letter Conversion Example ===")

    converter = GreekLatexConverter()

    # Convert to LaTeX
    text = "α particles, β rays, γ radiation"
    latex = converter.to_latex(text)
    print(f"Original: {text}")
    print(f"LaTeX: {latex}")

    # Convert from LaTeX back to Greek letters
    latex_text = r"\alpha particles, \beta rays"
    greek = converter.from_latex(latex_text)
    print(f"LaTeX: {latex_text}")
    print(f"Greek letters: {greek}")
    print()


def example_patterns():
    """Regular pattern example"""
    print("=== Regular Pattern Example ===")

    patterns = PatternCollection()

    text = "This  is a   test\n\n\nmultiple newlines"
    print(f"Original text: {repr(text)}")

    # Apply single pattern
    result = patterns.apply_pattern(text, "extra_whitespace")
    print(f"After applying whitespace pattern: {repr(result)}")

    # Apply all patterns
    result = patterns.apply_all(text)
    print(f"After applying all patterns: {repr(result)}")
    print()


def example_rules():
    """Document numbering rule engine example"""
    print("=== Rule Engine Example ===")

    rules = DocumentNumberingRuleEngine()

    text = "Chapter I Chapter 1 ①First item"
    print(f"Original text: {text}")

    result = rules.apply(text)
    print(f"After applying rules: {result}")
    print()


def example_file_cleaning():
    """File cleaning example"""
    print("=== File Cleaning Example ===")

    cleaner = TextCleaner()

    # Note: Actual file paths are required here
    # cleaner.clean_file("input.txt", "output.txt")
    print("Use cleaner.clean_file('input.txt', 'output.txt') to clean files")
    print()


if __name__ == "__main__":
    example_basic_cleaning()
    example_greek_conversion()
    example_patterns()
    example_rules()
    example_file_cleaning()

