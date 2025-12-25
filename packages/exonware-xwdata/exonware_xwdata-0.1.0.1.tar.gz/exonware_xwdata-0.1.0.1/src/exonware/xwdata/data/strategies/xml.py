#!/usr/bin/env python3
"""
#exonware/xwdata/src/exonware/xwdata/data/strategies/xml.py

XML Format Strategy

Lightweight XML-specific logic for metadata and references.
Serialization is handled by xwsystem.serialization.XmlSerializer.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 26-Oct-2025
"""

from typing import Any
from ...base import AFormatStrategy


class XMLFormatStrategy(AFormatStrategy):
    """
    XML format strategy providing xwdata-specific logic.
    
    Provides:
    - Metadata extraction (attributes, elements, structure)
    - Reference detection (@href, @xi:href, @xlink:href patterns)
    - Type mapping (XML types ↔ universal types)
    
    Does NOT provide:
    - Serialization (uses xwsystem.serialization.XmlSerializer)
    """
    
    def __init__(self):
        """Initialize XML strategy."""
        super().__init__()
        self._name = 'xml'
        self._extensions = ['xml', 'xhtml']
        
        # Reference patterns for XML
        self._reference_patterns = {
            'xml_href_ref': {
                'key': '@href',
                'pattern': r'^@href$'
            },
            'xml_xinclude_ref': {
                'key': '@xi:href',
                'pattern': r'^@xi:href$'
            },
            'xml_xlink_ref': {
                'key': '@xlink:href',
                'pattern': r'^@xlink:href$'
            },
            'xml_schema_location_ref': {
                'key': '@schemaLocation',
                'pattern': r'^@schemaLocation$'
            }
        }
        
        # Type mapping
        self._type_mapping = {
            'element': 'dict',
            'attribute': 'str',
            'text': 'str'
        }
    
    async def extract_metadata(self, data: Any, **opts) -> dict[str, Any]:
        """Extract XML-specific metadata."""
        metadata = {}
        
        if isinstance(data, dict):
            # Detect attributes (keys starting with @)
            attributes = [k for k in data.keys() if k.startswith('@')]
            if attributes:
                metadata['has_attributes'] = True
                metadata['attributes'] = attributes
                metadata['attribute_count'] = len(attributes)
            
            # Detect text content
            if '_text' in data:
                metadata['has_text'] = True
            
            # Detect element structure
            elements = [k for k in data.keys() if not k.startswith(('@', '_'))]
            if elements:
                metadata['elements'] = elements
                metadata['element_count'] = len(elements)
            
            # Detect metadata markers
            if '_metadata' in data:
                xml_meta = data['_metadata']
                if isinstance(xml_meta, dict):
                    metadata['element_type'] = xml_meta.get('element_type')
                    metadata['element_tag'] = xml_meta.get('element_tag')
        
        metadata['format'] = 'xml'
        return metadata
    
    async def detect_references(self, data: Any, **opts) -> list[dict[str, Any]]:
        """Detect XML-specific references."""
        references = []
        
        if isinstance(data, dict):
            # href attribute (most common)
            if '@href' in data and isinstance(data['@href'], str):
                references.append({
                    'type': 'xml_href_ref',
                    'uri': data['@href'],
                    'format': 'xml',
                    'metadata': {k: v for k, v in data.items() if k != '@href'}
                })
            
            # XInclude reference
            if '@xi:href' in data and isinstance(data['@xi:href'], str):
                references.append({
                    'type': 'xml_xinclude_ref',
                    'uri': data['@xi:href'],
                    'format': 'xml',
                    'metadata': {k: v for k, v in data.items() if k != '@xi:href'}
                })
            
            # XLink reference
            if '@xlink:href' in data and isinstance(data['@xlink:href'], str):
                references.append({
                    'type': 'xml_xlink_ref',
                    'uri': data['@xlink:href'],
                    'format': 'xml',
                    'metadata': {k: v for k, v in data.items() if k != '@xlink:href'}
                })
            
            # Schema location
            if '@schemaLocation' in data and isinstance(data['@schemaLocation'], str):
                references.append({
                    'type': 'xml_schema_location_ref',
                    'uri': data['@schemaLocation'],
                    'format': 'xml',
                    'metadata': {k: v for k, v in data.items() if k != '@schemaLocation'}
                })
            
            # Recursively check nested
            for key, value in data.items():
                if isinstance(value, (dict, list)) and not key.startswith('@'):
                    nested_refs = await self.detect_references(value)
                    references.extend(nested_refs)
        
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    nested_refs = await self.detect_references(item)
                    references.extend(nested_refs)
        
        return references


__all__ = ['XMLFormatStrategy']

