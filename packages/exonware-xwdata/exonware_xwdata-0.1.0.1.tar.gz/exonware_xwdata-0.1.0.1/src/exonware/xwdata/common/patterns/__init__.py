#!/usr/bin/env python3
"""
#exonware/xwdata/src/exonware/xwdata/common/patterns/__init__.py

Patterns Module

Generic design patterns and utilities.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 26-Oct-2025
"""

from .registry import Registry
from .factory import create_factory

__all__ = [
    'Registry',
    'create_factory',
]

