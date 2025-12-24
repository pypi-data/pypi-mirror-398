"""
Utility functions for langchain-apiverve.
"""

import re
from typing import List


def to_snake_case(name: str) -> str:
    """Convert a string to snake_case."""
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name)
    return name.lower().replace('-', '_').replace(' ', '_')


def to_pascal_case(name: str) -> str:
    """Convert a string to PascalCase."""
    words = re.split(r'[-_\s]+', name)
    return ''.join(word.capitalize() for word in words)


def truncate_text(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """Truncate text to a maximum length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix
