"""BibTeX standardization module.

This module provides comprehensive BibTeX standardization functionality including:
- Entry block standardization
- Comment block processing
- Preamble block handling
- String block processing
- Field validation and normalization

The main class StandardizeBib provides a unified interface for standardizing
BibTeX files according to consistent formatting rules.

Classes:
    StandardizeBib: Main standardization class that processes BibTeX files
        and returns standardized output with error reporting.
"""

__all__ = ["StandardizeBib"]

from .standardize_bib import StandardizeBib
