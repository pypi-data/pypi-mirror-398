"""
SanTOK Package
A comprehensive text tokenization system with mathematical analysis and statistical features
"""

__version__ = "1.0.0"
__author__ = "Santosh Chavala"
__email__ = "chavalasantosh@example.com"

# Import the main class and convenience functions
from .santok import (
    TextTokenizationEngine, 
    tokenize_text, 
    analyze_text_comprehensive, 
    generate_text_summary
)

__all__ = [
    'TextTokenizationEngine',
    'tokenize_text', 
    'analyze_text_comprehensive',
    'generate_text_summary'
]