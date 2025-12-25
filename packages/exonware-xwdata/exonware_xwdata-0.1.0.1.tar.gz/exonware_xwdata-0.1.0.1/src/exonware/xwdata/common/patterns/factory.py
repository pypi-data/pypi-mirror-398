#!/usr/bin/env python3
"""
#exonware/xwdata/src/exonware/xwdata/common/patterns/factory.py

Generic Factory Pattern

Factory helpers for creating objects.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 26-Oct-2025
"""

from typing import Any, Callable


def create_factory(creator: Callable[..., Any], **default_kwargs) -> Callable[..., Any]:
    """
    Create a factory function with default arguments.
    
    Args:
        creator: Creator function
        **default_kwargs: Default keyword arguments
        
    Returns:
        Factory function
    """
    def factory(**kwargs):
        # Merge default and provided kwargs
        merged_kwargs = {**default_kwargs, **kwargs}
        return creator(**merged_kwargs)
    
    return factory


__all__ = ['create_factory']

