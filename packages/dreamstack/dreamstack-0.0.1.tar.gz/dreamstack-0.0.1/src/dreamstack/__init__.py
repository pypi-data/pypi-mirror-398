# -*- coding: utf-8 -*-


# =============================================================================
# Docstring
# =============================================================================

"""
Dreamstack - A Python Library
=============================

Dreamstack is a demonstration library for publishing to PyPI, showcasing best practices
in Python package development.

This package provides utilities for greeting and message formatting, with comprehensive
error handling and type safety.

Examples:
    Basic usage::

        >>> from dreamstack import hello
        >>> hello("Scape")
        'Hello, Scape! Welcome to the dreamstack library.'

    Advanced usage::

        >>> from dreamstack import greet, format_message
        >>> greet("Alice", "Hi")
        'Hi, Alice!'
        >>> format_message("Bob", "Task done", prefix="[INFO]")
        '[INFO] Bob: Task done'

Attributes:
    __version__: The version string for this package.
    __version_info__: A tuple of version components.

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Standard Library
from typing import Iterable

# Import | Local
from dreamstack.__version__ import __version__, __version_info__
from dreamstack.core import format_message, greet, hello

# =============================================================================
# Package Initialization
# =============================================================================

# Enable namespace package support
__path__: Iterable[str]
__path__ = __import__(name="pkgutil").extend_path(
    __path__,
    __name__,
)

# =============================================================================
# Exports
# =============================================================================

# Public API exports
__all__: list[str] = [
    # Version information
    "__version__",
    "__version_info__",
    # Core functions
    "hello",
    "greet",
    "format_message",
]
