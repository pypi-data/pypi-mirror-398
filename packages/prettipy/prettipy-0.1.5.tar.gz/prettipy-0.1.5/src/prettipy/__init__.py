"""
Prettipy - Beautiful Python Code to PDF Converter

A Python package that converts Python source code into beautifully formatted,
syntax-highlighted PDF documents.
"""

__version__ = "0.1.4"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .core import PrettipyConverter
from .config import PrettipyConfig

__all__ = ["PrettipyConverter", "PrettipyConfig"]
