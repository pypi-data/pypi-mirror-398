#!/usr/bin/env python3
"""
#exonware/xwdata/src/exonware/xwdata/data/metadata/universal.py

Universal Metadata System

Preserves format-specific semantics for perfect roundtrips between formats.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 26-Oct-2025
"""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class UniversalMetadata:
    """
    Universal metadata for format-agnostic data preservation.
    
    Preserves:
    - Source format information
    - Reserved characters and special keys
    - Type information
    - Structural information
    - Format-specific semantics
    """
    
    source_format: str = ''
    reserved_chars: list[str] = field(default_factory=list)
    reserved_keys: list[str] = field(default_factory=list)
    has_schema: bool = False
    schema_uri: Optional[str] = None
    has_attributes: bool = False
    attributes: list[str] = field(default_factory=list)
    has_text: bool = False
    elements: list[str] = field(default_factory=list)
    multi_document: bool = False
    document_count: int = 1
    custom_fields: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            'source_format': self.source_format,
            'reserved_chars': self.reserved_chars,
            'reserved_keys': self.reserved_keys,
            'has_schema': self.has_schema,
            'schema_uri': self.schema_uri,
            'has_attributes': self.has_attributes,
            'attributes': self.attributes,
            'has_text': self.has_text,
            'elements': self.elements,
            'multi_document': self.multi_document,
            'document_count': self.document_count,
            'custom_fields': self.custom_fields
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'UniversalMetadata':
        """Create from dictionary."""
        return cls(
            source_format=data.get('source_format', ''),
            reserved_chars=data.get('reserved_chars', []),
            reserved_keys=data.get('reserved_keys', []),
            has_schema=data.get('has_schema', False),
            schema_uri=data.get('schema_uri'),
            has_attributes=data.get('has_attributes', False),
            attributes=data.get('attributes', []),
            has_text=data.get('has_text', False),
            elements=data.get('elements', []),
            multi_document=data.get('multi_document', False),
            document_count=data.get('document_count', 1),
            custom_fields=data.get('custom_fields', {})
        )


__all__ = ['UniversalMetadata']

