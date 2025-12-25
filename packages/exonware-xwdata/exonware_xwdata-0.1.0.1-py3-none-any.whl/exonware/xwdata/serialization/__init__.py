#!/usr/bin/env python3
"""
#exonware/xwdata/src/exonware/xwdata/serialization/__init__.py

XWData Extended Serialization

xwdata-specific serializers that extend xwsystem's base serialization
with additional format support (JSON5, JSONL, enhanced YAML, etc.).

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 26-Oct-2025
"""

from .registry import XWDataSerializerRegistry
from .json5 import JSON5Serializer
from .jsonlines import JSONLinesSerializer

__all__ = [
    'XWDataSerializerRegistry',
    'JSON5Serializer',
    'JSONLinesSerializer',
]

