#!/usr/bin/env python3
"""
#exonware/xwdata/src/exonware/xwdata/data/metadata/processor.py

Metadata Processor Implementation

Orchestrates metadata extraction using format strategies.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 26-Oct-2025
"""

from typing import Any, Optional
from exonware.xwsystem import get_logger

from ...base import AMetadataProcessor
from ...config import XWDataConfig
from ...contracts import IFormatStrategy
from .universal import UniversalMetadata
from .extractor import MetadataExtractor

logger = get_logger(__name__)


class MetadataProcessor(AMetadataProcessor):
    """
    Metadata processor orchestrating extraction and application.
    
    Coordinates:
    - Format-specific metadata extraction via strategies
    - Universal metadata creation
    - Metadata application for target formats
    """
    
    def __init__(self, config: Optional[XWDataConfig] = None):
        """
        Initialize metadata processor.
        
        Args:
            config: Optional configuration
        """
        super().__init__()
        self._config = config or XWDataConfig.default()
        self._extractor = MetadataExtractor()
    
    async def extract(
        self,
        data: Any,
        strategy: IFormatStrategy,
        **opts
    ) -> dict[str, Any]:
        """
        Extract metadata using format strategy.
        
        Args:
            data: Data to extract metadata from
            strategy: Format strategy
            **opts: Additional options
            
        Returns:
            Metadata dictionary
        """
        if not self._config.metadata.enable_universal_metadata:
            return {}
        
        # Use strategy to extract format-specific metadata
        format_metadata = await strategy.extract_metadata(data, **opts)
        
        # Convert to universal metadata if configured
        if self._config.metadata.mode.name == 'UNIVERSAL':
            universal = await self._extractor.extract_universal(data, format_metadata)
            return universal.to_dict()
        
        return format_metadata
    
    async def apply(
        self,
        data: Any,
        metadata: dict[str, Any],
        target_format: str,
        **opts
    ) -> Any:
        """
        Apply metadata for target format.
        
        Uses format-specific strategies to apply metadata based on target format capabilities.
        Different formats handle metadata differently (e.g., JSON uses $schema, XML uses attributes).
        
        Args:
            data: Data to apply metadata to
            metadata: Metadata to apply
            target_format: Target format name (e.g., 'json', 'xml', 'yaml')
            **opts: Additional options
            
        Returns:
            Data with applied metadata
            
        Priority Alignment:
        - Usability: Simple, format-aware metadata application
        - Maintainability: Strategy-based approach for extensibility
        - Performance: Efficient format-specific handling
        """
        if not metadata:
            return data
        
        # Get format strategy for target format
        from ...data.strategies.registry import FormatStrategyRegistry
        registry = FormatStrategyRegistry()
        strategy = registry.get(target_format.lower())
        
        if not strategy:
            # No strategy available - return data unchanged
            logger.debug(f"No strategy available for format '{target_format}', skipping metadata application")
            return data
        
        # Apply metadata based on format capabilities
        # Different formats handle metadata differently:
        # - JSON: Uses $schema, @context (JSON-LD), reserved keys
        # - XML: Uses attributes, namespaces, processing instructions
        # - YAML: Uses directives, tags, comments
        # - Other formats: Format-specific mechanisms
        
        result = data
        
        # Strategy 1: Schema URI (JSON Schema, XML Schema, etc.)
        if 'schema_uri' in metadata and metadata['schema_uri']:
            result = await self._apply_schema_uri(result, metadata['schema_uri'], target_format, strategy)
        
        # Strategy 2: Format-specific reserved keys/attributes
        if 'reserved_keys' in metadata and metadata['reserved_keys']:
            result = await self._apply_reserved_keys(result, metadata['reserved_keys'], target_format, strategy)
        
        # Strategy 3: Type information
        if 'type_hints' in metadata and metadata['type_hints']:
            result = await self._apply_type_hints(result, metadata['type_hints'], target_format, strategy)
        
        # Strategy 4: Format-specific metadata (delegate to strategy if it supports it)
        if 'format_specific' in metadata:
            result = await self._apply_format_specific(result, metadata['format_specific'], target_format, strategy)
        
        return result
    
    async def _apply_schema_uri(
        self,
        data: Any,
        schema_uri: str,
        format: str,
        strategy: Any
    ) -> Any:
        """Apply schema URI to data based on format."""
        if isinstance(data, dict):
            result = data.copy()
            
            # JSON/YAML: Use $schema
            if format.lower() in ('json', 'yaml', 'json5'):
                result['$schema'] = schema_uri
            # XML: Could use xsi:schemaLocation attribute
            elif format.lower() == 'xml':
                # XML schema location is typically set at root element
                # For dict representation, we add it as metadata
                if not isinstance(result.get('_attributes'), dict):
                    result['_attributes'] = {}
                result['_attributes']['xsi:schemaLocation'] = schema_uri
            
            return result
        
        return data
    
    async def _apply_reserved_keys(
        self,
        data: Any,
        reserved_keys: list[str],
        format: str,
        strategy: Any
    ) -> Any:
        """Apply reserved keys to data (preserve format-specific keys)."""
        if isinstance(data, dict):
            result = data.copy()
            
            # Preserve existing reserved keys that are in the metadata
            # This ensures format-specific metadata is maintained during conversion
            for key in reserved_keys:
                if key in result:
                    # Key already exists, preserve it
                    continue
                # New reserved keys are typically not added, only preserved
            
            return result
        
        return data
    
    async def _apply_type_hints(
        self,
        data: Any,
        type_hints: dict[str, Any],
        format: str,
        strategy: Any
    ) -> Any:
        """Apply type hints to data (format-specific type annotations)."""
        # Type hints are primarily used for validation and conversion
        # Different formats handle types differently (JSON native, YAML tags, XML types)
        # For now, preserve type information in metadata rather than embedding
        if isinstance(data, dict) and isinstance(type_hints, dict):
            result = data.copy()
            # Store type hints as metadata for validation
            if '_type_hints' not in result:
                result['_type_hints'] = type_hints
            
            return result
        
        return data
    
    async def _apply_format_specific(
        self,
        data: Any,
        format_metadata: dict[str, Any],
        format: str,
        strategy: Any
    ) -> Any:
        """Apply format-specific metadata."""
        if isinstance(data, dict):
            result = data.copy()
            
            # Merge format-specific metadata into data
            # Format-specific metadata is applied according to format conventions
            for key, value in format_metadata.items():
                # Only apply if not conflicting with existing keys
                if key not in result or result[key] != value:
                    # Check if key is a reserved key for this format
                    if format.lower() in ('json', 'yaml'):
                        # JSON/YAML reserved keys start with $ or @
                        if key.startswith(('$', '@')):
                            result[key] = value
                    elif format.lower() == 'xml':
                        # XML attributes
                        if key.startswith('@'):
                            if not isinstance(result.get('_attributes'), dict):
                                result['_attributes'] = {}
                            result['_attributes'][key[1:]] = value
            
            return result
        
        return data


__all__ = ['MetadataProcessor']

