"""
jexpand - Enhanced file expansion using Jinja2 templates
"""

from .main import expand_file, JinjaFileExpander, main

__version__ = "1.0.4"
__all__ = ["expand_file", "JinjaFileExpander", "main"]


if __name__ == "__main__":
    main() 
