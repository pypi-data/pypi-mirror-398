"""
One-line setup - Minimal code for maximum functionality.

Usage:
    from apex.setup import setup
    
    client = setup()  # Everything is ready!
"""

from apex.quickstart import quick_setup, auto_setup

# Simple alias
setup = auto_setup

__all__ = ["setup"]







