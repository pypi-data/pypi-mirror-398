"""
TurboSEO - SEO content toolkit that writes human, not AI.

Based on Wikipedia's "Signs of AI Writing" guidelines, TurboSEO helps you
create content that ranks well and sounds authentically human.
"""

__version__ = "0.1.0"
__author__ = "Thijs"

from turboseo.analyzers import (
    analyze_keywords,
    analyze_readability,
    analyze_seo,
    analyze_writing_standards,
)

__all__ = [
    "__version__",
    "analyze_writing_standards",
    "analyze_readability",
    "analyze_keywords",
    "analyze_seo",
]
