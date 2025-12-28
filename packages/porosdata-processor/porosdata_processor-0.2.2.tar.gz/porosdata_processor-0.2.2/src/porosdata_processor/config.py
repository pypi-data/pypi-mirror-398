# -*- coding: utf-8 -*-
"""Configuration and Constants Management"""

# Default configuration
DEFAULT_ENCODING = "utf-8"
DEFAULT_CHUNK_SIZE = 1024 * 4  # 4KB

# Supported file extensions
# Note: LaTeX space cleaning functionality applies to all text file formats containing LaTeX formulas
# Including but not limited to: Markdown (.md), JSON (.json), plain text (.txt), LaTeX source files (.tex, .latex), etc.
SUPPORTED_EXTENSIONS = {".txt", ".md", ".tex", ".latex", ".json"}

# Log level
LOG_LEVEL = "INFO"

# Default cleaning options
# Note: Basic cleaning features (normalize_whitespace, remove_extra_spaces) have been moved to default pipeline
# Only advanced optional features are kept here
DEFAULT_CLEAN_OPTIONS = {
    # Whether to clean extra spaces inside LaTeX mathematical formulas (e.g.: \mathbf { X } -> \mathbf{X})
    # Disabled by default to avoid affecting existing behavior, enable explicitly when needed
    "clean_latex_math_spaces": False,
}

