#!/usr/bin/env python3
"""
#exonware/xwdata/src/exonware/xwdata/data/references/patterns.py

Reference Patterns

Common reference patterns across formats.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 26-Oct-2025
"""

from typing import Any


class ReferencePatterns:
    """Common reference patterns across data formats."""
    
    # JSON reference patterns
    JSON_PATTERNS = {
        'json_schema_ref': r'\$ref',
        'json_ld_id': r'@id',
        'json_ld_type': r'@type'
    }
    
    # XML reference patterns
    XML_PATTERNS = {
        'xml_href': r'@href',
        'xml_xinclude': r'@xi:href',
        'xml_xlink': r'@xlink:href',
        'xml_schema_location': r'@schemaLocation'
    }
    
    # YAML reference patterns
    YAML_PATTERNS = {
        'yaml_anchor': r'\*\w+',
        'yaml_merge': r'<<'
    }
    
    @classmethod
    def get_all_patterns(cls) -> dict[str, dict[str, str]]:
        """Get all reference patterns."""
        return {
            'json': cls.JSON_PATTERNS,
            'xml': cls.XML_PATTERNS,
            'yaml': cls.YAML_PATTERNS
        }


__all__ = ['ReferencePatterns']

