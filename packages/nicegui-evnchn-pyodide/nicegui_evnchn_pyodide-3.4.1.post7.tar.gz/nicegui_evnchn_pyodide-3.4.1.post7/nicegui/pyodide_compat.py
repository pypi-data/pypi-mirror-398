"""
Pyodide compatibility utilities for NiceGUI.

This module provides utilities to detect when running in Pyodide
and handle conditional imports for pure-Python compatibility.
"""
import sys


def is_pyodide() -> bool:
    """Check if running in Pyodide environment."""
    return 'pyodide' in sys.modules or hasattr(sys, '_emscripten_info')


# Set a flag for easy checking
IS_PYODIDE = is_pyodide()
