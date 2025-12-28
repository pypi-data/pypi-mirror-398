"""
mlleak - ML Data Leakage & Split Sanity Checker

Detects data leakage and bad train/test splits in machine learning workflows.
"""

from .detector import report

__version__ = "0.1.0"
__all__ = ["report"]
