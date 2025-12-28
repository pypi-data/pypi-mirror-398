# -*- coding: utf-8 -*-
"""Document Structure and Numbering Normalization Rule Engine

This module focuses on **document structure-related numbering normalization**, including:
- Chapter numbers (Chapter 1, 第1章, etc.)
- Section numbers (1.1, 1.1.1, etc.)
- Roman numerals (I, II, III, iv, etc.)
- Circled index numbers (①, ②, ③, etc.)

Does not handle:
- LaTeX formula syntax
- Greek letter to LaTeX command conversion (see `greek_latex_converter.py`)
"""

import re
from typing import List, Callable, Optional
from .plugin_system import PluginRegistry


class DocumentNumberingRuleEngine:
    """Document Structure and Numbering Normalization Rule Engine"""
    
    def __init__(self):
        self.rules: List[Callable[[str], str]] = []
        self._init_default_rules()
    
    def _init_default_rules(self):
        """Initialize default rule set"""
        # Chapter heading normalization (Chapter 1, 第1章, etc.)
        self.add_rule(self._normalize_chapter_headings)
        # Section numbering normalization (1.1, 1.1.1, etc.)
        self.add_rule(self._normalize_section_numbering)
        # Roman numeral normalization (I, II, III, iv, etc. → Arabic numerals)
        self.add_rule(self._normalize_roman_numerals_to_arabic)
        # Circled index number normalization (①, ②, ③, etc. → regular numbers)
        self.add_rule(self._normalize_circled_index_numbers)
    
    def add_rule(self, rule_func: Callable[[str], str]):
        """Add cleaning rule function"""
        self.rules.append(rule_func)
    
    def remove_rule(self, rule_func: Callable[[str], str]):
        """Remove rule function"""
        if rule_func in self.rules:
            self.rules.remove(rule_func)
    
    def apply(self, text: str) -> str:
        """Apply all rules to text"""
        result = text
        for rule in self.rules:
            result = rule(result)
        return result
    
    def _normalize_chapter_headings(self, text: str) -> str:
        """Normalize chapter headings (e.g.: 第1章, 第1节, Chapter 1, etc.)"""
        # Chinese chapter numbers: 第X章, 第X节
        text = re.sub(r'第([0-9]+)章', r'第\1章', text)
        text = re.sub(r'第([0-9]+)节', r'第\1节', text)
        
        # English chapter numbers: Chapter X, Chapter X.
        text = re.sub(r'Chapter\s+([0-9]+)\s*\.', r'Chapter \1', text)
        text = re.sub(r'Chapter\s+([0-9]+)', r'Chapter \1', text)
        
        return text
    
    def _normalize_section_numbering(self, text: str) -> str:
        """Normalize section numbering format (e.g.: 1.1, 1.1.1)

        Note: Add line start anchor to avoid accidentally affecting dates and version numbers in main text
        """
        lines = text.split('\n')
        processed_lines = []

        for line in lines:
            # Only process section number format at line start, avoid affecting X.X.X in main text
            # Match section numbers at line start (followed by title content)
            line = re.sub(r'^(\d+)\.(\d+)\.(\d+)\s+', r'\1.\2.\3 ', line)
            line = re.sub(r'^(\d+)\.(\d+)\s+', r'\1.\2 ', line)
            processed_lines.append(line)

        return '\n'.join(processed_lines)
    
    def _normalize_roman_numerals_to_arabic(self, text: str) -> str:
        """Normalize standalone Roman numerals to Arabic numerals (I, II, III → 1, 2, 3)

        Note: Use negative lookahead to avoid accidentally affecting Roman numerals in brackets [] or parentheses () (usually citation markers)
        """
        # Roman numeral to Arabic numeral mapping (1-20)
        roman_to_arabic = {
            'I': '1', 'II': '2', 'III': '3', 'IV': '4', 'V': '5',
            'VI': '6', 'VII': '7', 'VIII': '8', 'IX': '9', 'X': '10',
            'XI': '11', 'XII': '12', 'XIII': '13', 'XIV': '14', 'XV': '15',
            'XVI': '16', 'XVII': '17', 'XVIII': '18', 'XIX': '19', 'XX': '20'
        }

        # Lowercase Roman numerals
        roman_to_arabic_lower = {k.lower(): v for k, v in roman_to_arabic.items()}
        roman_to_arabic.update(roman_to_arabic_lower)

        # Match standalone Roman numerals (with word boundaries, but exclude Roman numerals in []() )
        def replace_roman(match):
            roman = match.group(1)
            if roman in roman_to_arabic:
                return match.group(0).replace(roman, roman_to_arabic[roman])
            return match.group(0)

        # Exclude Roman numerals surrounded by square brackets (citation markers)
        # Method: Find all standalone Roman numerals, but skip those surrounded by []

        # Strategy change: Do not convert any Roman numerals surrounded by square brackets, as they are usually citation markers
        # Only convert truly standalone Roman numerals (surrounded by non-alphanumeric characters)

        def replace_roman(match):
            roman = match.group(1)
            start = match.start()
            end = match.end()

            # Check if Roman numeral is directly surrounded by square brackets
            # Method: Look forward for nearest [, look backward for nearest ]
            # Only consider surrounded if nearest [ is before start, and nearest ] is after end

            # Look forward for nearest [
            before_part = text[:start]
            last_open_bracket = before_part.rfind('[')

            # Look backward for nearest ]
            after_part = text[end:]
            first_close_bracket = after_part.find(']')

            # If direct surrounding square brackets found, do not convert
            if (last_open_bracket != -1 and first_close_bracket != -1 and
                last_open_bracket < start and end + first_close_bracket <= len(text)):
                # Additional check: ensure this bracket pair is not interfered by other brackets
                bracket_content = text[last_open_bracket:end + first_close_bracket + 1]
                if bracket_content.count('[') == 1 and bracket_content.count(']') == 1:
                    return match.group(0)

            # Otherwise, convert normally
            if roman in roman_to_arabic:
                return roman_to_arabic[roman]
            return roman

        pattern = r'\b([IVX]+)\b'
        text = re.sub(pattern, replace_roman, text)
        text = re.sub(pattern, replace_roman, text)
        return text
    
    def _normalize_circled_index_numbers(self, text: str) -> str:
        """Normalize circled index numbers (e.g.: ①, ②, ③ → 1, 2, 3)"""
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
    Create custom "document numbering normalization" rule function
    
    Args:
        pattern: Regular expression pattern
        replacement: Replacement string
        
    Returns:
        Rule function
    """
    compiled_pattern = re.compile(pattern)
    
    def rule(text: str) -> str:
        return compiled_pattern.sub(replacement, text)
    
    return rule


@PluginRegistry.register("document_numbering_rules")
def apply_document_numbering_rules(text: str) -> str:
    """Apply all document numbering normalization rules (usable through pipeline)"""
    engine = DocumentNumberingRuleEngine()
    return engine.apply(text)


