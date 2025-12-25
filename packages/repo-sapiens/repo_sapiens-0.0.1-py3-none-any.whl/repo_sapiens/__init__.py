"""
hello-python-test-shireadmin

A simple hello world package for testing Python package distribution.
"""

__version__ = "0.0.1"
__author__ = "Test Author"
__email__ = "test@example.com"

from .core import greet, get_greeting

__all__ = ["greet", "get_greeting", "__version__"]
