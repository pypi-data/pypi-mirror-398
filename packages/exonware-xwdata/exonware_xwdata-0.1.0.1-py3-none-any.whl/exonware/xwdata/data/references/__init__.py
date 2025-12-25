#!/usr/bin/env python3
"""
#exonware/xwdata/src/exonware/xwdata/data/references/__init__.py

Reference Resolution System

Detection and resolution of cross-references in data.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 26-Oct-2025
"""

from .detector import ReferenceDetector
from .resolver import ReferenceResolver
from .patterns import ReferencePatterns

__all__ = [
    'ReferenceDetector',
    'ReferenceResolver',
    'ReferencePatterns',
]

