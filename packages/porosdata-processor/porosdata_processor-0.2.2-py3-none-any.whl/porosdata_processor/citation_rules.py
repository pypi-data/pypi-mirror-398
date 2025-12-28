# -*- coding: utf-8 -*-
"""Citation Marker Normalization Rules

This module focuses on standardizing citation markers, including:
- Full-width brackets to half-width brackets
- Inner space cleanup
- Outer spacing optimization
- Protection of Roman numeral citation markers

Does not handle:
- Markdown link syntax [text](url)
- Document structure numbering (see document_numbering_rules.py)
"""

import re
from typing import List, Callable
from .plugin_system import PluginRegistry


class CitationRulesEngine:
    """Citation Marker Normalization Rule Engine"""

    def __init__(self):
        self.rules: List[Callable[[str], str]] = []
        self._init_default_rules()

    def _init_default_rules(self):
        """Initialize default rule set"""
        # Full-width brackets to half-width
        self.add_rule(self._normalize_fullwidth_brackets)
        # Inner space cleanup
        self.add_rule(self._normalize_inner_spaces)
        # Outer spacing optimization
        self.add_rule(self._optimize_outer_spacing)

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

        # Finally restore protected Roman numeral citation markers
        result = re.sub(r'__ROMAN_CITATION_([IVXLCDM]+)__', r'\1', result)

        return result

    def _normalize_fullwidth_brackets(self, text: str) -> str:
        """Convert full-width brackets to half-width brackets"""
        # 【N】 → [N] (Chinese full-width square brackets)
        text = re.sub(r'【([^\[\]]*)】', r'[\1]', text)
        # ［N］ → [N] (full-width square brackets)
        text = re.sub(r'［([^\[\]]*)］', r'[\1]', text)
        # 〔N〕 → [N] (full-width hexagonal brackets)
        text = re.sub(r'〔([^\[\]]*)〕', r'[\1]', text)

        return text

    def _normalize_inner_spaces(self, text: str) -> str:
        """Clean extra spaces inside citation markers

        For example: [ 12 ] → [12], [ 1, 2 ] → [1,2], [ I ] → [I]
        Note: Protects Roman numeral citation markers to prevent accidental damage by subsequent Roman numeral conversion rules
        """
        # Match content within square brackets, clean internal spaces
        def clean_inner(match):
            content = match.group(1)
            # Clean spaces in content
            cleaned = re.sub(r'\s+', '', content)

            # If cleaned content is pure Roman numerals, mark as protected state
            # Use special prefix to avoid being affected by document_numbering_rules Roman numeral conversion
            if re.match(r'^[IVXLCDM]+$', cleaned):
                return f'[__ROMAN_CITATION_{cleaned}__]'
            else:
                return f'[{cleaned}]'

        # Only match square brackets containing combinations of numbers, Roman numerals, commas, hyphens
        # Avoid matching Markdown links [text](url)
        pattern = r'\[([IVXLCDM\d,\-\s]+)\]'
        text = re.sub(pattern, clean_inner, text)

        return text

    def _optimize_outer_spacing(self, text: str) -> str:
        """Optimize outer spacing of citation markers

        - Inline citations: Remove unnecessary extra spaces before markers (text  [1] → text[1])
        - Line-start lists: Ensure one standard space after markers ([1]Author → [1] Author)
        """
        lines = text.split('\n')
        processed_lines = []

        for line in lines:
            # Handle inline citations: Remove one or more spaces before markers (but preserve spaces after punctuation)
            # Only match spaces+markers after letters/numbers/Chinese characters
            line = re.sub(r'([a-zA-Z0-9\u4e00-\u9fa5])\s{1,}(\[[IVXLCDM\d,\-]+\])', r'\1\2', line)

            # Handle line-start lists: Ensure one space after markers (if followed by non-space character)
            # But avoid duplicate addition when space already exists after marker
            line = re.sub(r'^(\[[IVXLCDM\d,\-]+\])(?!\s)(\S)', r'\1 \2', line)

            processed_lines.append(line)

        return '\n'.join(processed_lines)


@PluginRegistry.register("citation_rules")
def apply_citation_rules(text: str) -> str:
    """Apply all citation marker normalization rules (usable through pipeline)"""
    engine = CitationRulesEngine()
    return engine.apply(text)
