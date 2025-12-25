#!/usr/bin/env python3
"""
#exonware/xwdata/src/exonware/xwdata/data/metadata/extractor.py

Metadata Extractor Implementation

Extracts universal metadata from format-specific metadata.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 26-Oct-2025
"""

from typing import Any
from exonware.xwsystem import get_logger

from .universal import UniversalMetadata

logger = get_logger(__name__)


class MetadataExtractor:
    """
    Extractor for universal metadata from format-specific metadata.
    
    Converts format-specific metadata into universal metadata
    for format-agnostic preservation.
    """
    
    def __init__(self):
        """Initialize metadata extractor."""
        pass
    
    async def extract_universal(
        self,
        data: Any,
        format_metadata: dict[str, Any]
    ) -> UniversalMetadata:
        """
        Extract universal metadata from format-specific metadata.
        
        Args:
            data: Original data
            format_metadata: Format-specific metadata from strategy
            
        Returns:
            UniversalMetadata instance
        """
        return UniversalMetadata(
            source_format=format_metadata.get('format', 'unknown'),
            reserved_chars=format_metadata.get('reserved_chars', []),
            reserved_keys=format_metadata.get('reserved_keys', []),
            has_schema=format_metadata.get('has_schema', False),
            schema_uri=format_metadata.get('schema_uri'),
            has_attributes=format_metadata.get('has_attributes', False),
            attributes=format_metadata.get('attributes', []),
            has_text=format_metadata.get('has_text', False),
            elements=format_metadata.get('elements', []),
            multi_document=format_metadata.get('multi_document', False),
            document_count=format_metadata.get('document_count', 1),
            custom_fields={
                k: v for k, v in format_metadata.items()
                if k not in ['format', 'reserved_chars', 'reserved_keys',
                           'has_schema', 'schema_uri', 'has_attributes',
                           'attributes', 'has_text', 'elements',
                           'multi_document', 'document_count']
            }
        )


__all__ = ['MetadataExtractor']

