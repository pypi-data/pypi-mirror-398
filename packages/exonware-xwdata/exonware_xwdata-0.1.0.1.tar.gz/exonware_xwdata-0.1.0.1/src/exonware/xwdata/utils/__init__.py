#!/usr/bin/env python3
"""
#exonware/xwdata/src/exonware/xwdata/utils/__init__.py

Utility functions for XWData.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 29-Oct-2025
"""

from .format_helpers import (
    detect_format_fast,
    is_core_format,
    get_serializer_for_format,
    get_serializer_for_path,
    supports_partial_access,
    supports_canonical,
    supports_streaming
)

__all__ = [
    'detect_format_fast',
    'is_core_format',
    'get_serializer_for_format',
    'get_serializer_for_path',
    'supports_partial_access',
    'supports_canonical',
    'supports_streaming'
]

