"""
Rainfall: Run Python with AI-powered stub functions.

Functions with `...` as their body are automatically executed by an LLM
based on their name, signature, and docstring.
"""

from rainfall.core import execute_with_rainfall
from rainfall.config import RainfallConfig

__version__ = "0.1.0"
__all__ = ["execute_with_rainfall", "RainfallConfig"]
