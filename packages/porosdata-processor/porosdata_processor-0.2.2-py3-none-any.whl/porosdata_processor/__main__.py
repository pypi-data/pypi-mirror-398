# -*- coding: utf-8 -*-
"""porosdata_processor package main entry point

Allows running demo code via `python -m porosdata_processor`
"""

import sys
import os

# Set Windows console encoding to UTF-8
if sys.platform == "win32":
    # Method 1: Set environment variables
    os.environ["PYTHONIOENCODING"] = "utf-8"
    # Method 2: Try to set console code page (if possible)
    try:
        import subprocess
        subprocess.run(["chcp", "65001"], shell=True, capture_output=True)
    except:
        pass
    # Method 3: Reconfigure standard output encoding
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

from porosdata_processor import __version__, TextCleaner
from porosdata_processor.greek_latex_converter import GreekLatexConverter


def main():
    """Main entry function"""
    run_demo()


def run_demo():
    """Run demo code"""
    print("=" * 60)
    print(f"porosdata_processor v{__version__} - Text Cleaning Toolkit")
    print("=" * 60)
    print()
    
    # Basic usage example
    print("Basic Usage Example:")
    print("-" * 60)
    
    cleaner = TextCleaner()
    test_text = "This is a  test text. Contains α particles, β rays."
    
    print(f"Original text: {test_text}")
    cleaned = cleaner.clean(test_text)
    print(f"After cleaning: {cleaned}")
    print()
    
    # Greek letter conversion example
    print("Greek Letter Conversion Example:")
    print("-" * 60)
    
    converter = GreekLatexConverter()
    greek_text = "α particles, β rays, γ radiation"
    latex_text = converter.to_latex(greek_text)
    
    print(f"Original: {greek_text}")
    print(f"Converted to LaTeX: {latex_text}")
    print()
    
    print("=" * 60)
    print("Tip: More examples available in porosdata_processor/examples/ directory")
    print("=" * 60)


if __name__ == "__main__":
    """Run demo code"""
    main()

