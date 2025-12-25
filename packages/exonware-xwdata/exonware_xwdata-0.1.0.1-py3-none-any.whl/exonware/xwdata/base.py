#!/usr/bin/env python3
"""
#exonware/xwdata/src/exonware/xwdata/base.py

XWData Abstract Base Classes

This module defines abstract base classes that extend interfaces from contracts.py.
Following GUIDELINES_DEV.md: All abstract classes start with 'A' and extend 'I' interfaces.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 26-Oct-2025
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Union, AsyncIterator
from pathlib import Path
import sys
import site
from exonware.xwsystem import get_logger

from .contracts import (
    IData, IDataEngine, IDataNode, IFormatStrategy,
    IMetadataProcessor, IReferenceDetector, IReferenceResolver,
    ICacheManager, INodeFactory, IXWDataSerializer
)
from .defs import DataFormat, MergeStrategy, SerializationMode, COWMode

logger = get_logger(__name__)


# ==============================================================================
# ABSTRACT DATA
# ==============================================================================

class AData(IData):
    """
    Abstract base class for data implementations.
    
    Provides common functionality for XWData implementations.
    Extends IData interface.
    """
    
    def __init__(self):
        """Initialize abstract data."""
        self._node: Optional[IDataNode] = None
        self._engine: Optional[IDataEngine] = None
        self._metadata: dict[str, Any] = {}
    
    def get_metadata(self) -> dict[str, Any]:
        """Get metadata dictionary."""
        return self._metadata.copy()
    
    def get_format(self) -> Optional[str]:
        """Get format information."""
        return self._metadata.get('format')
    
    def __str__(self) -> str:
        """
        String representation - formats data using set_format (or detected_format as fallback).
        
        Format priority:
        1. set_format (user override) - if user called set_format()
        2. detected_format (original) - format detected from file
        3. JSON (default) - fallback if neither set
        
        Format-agnostic: Uses universal serialization options for clean, maintainable code.
        """
        if not self._node:
            return "XWData(empty)"
        
        # Priority: set_format > detected_format > 'JSON'
        active_format = (
            self._metadata.get('set_format') or 
            self._metadata.get('detected_format') or 
            'JSON'
        )
        
        # Get native data
        native_data = self.to_native()
        
        # Format-agnostic serialization using universal options
        try:
            from exonware.xwsystem.serialization.auto_serializer import AutoSerializer
            
            auto_serializer = AutoSerializer()
            
            # Use universal options for pretty-printing
            result = auto_serializer.detect_and_serialize(
                native_data,
                format_hint=active_format,
                pretty=True,         # Always pretty for printing
                ensure_ascii=False,  # Keep Unicode
                indent=2,            # Standard indentation
                encoding='utf-8'
            )
            
            return result if isinstance(result, str) else result.decode('utf-8')
        
        except Exception as e:
            # Fallback: JSON pretty-print
            logger.debug(f"Format serialization failed in __str__: {e}, using JSON fallback")
            import json
            return json.dumps(native_data, indent=2, ensure_ascii=False, default=str)
    
    def __repr__(self) -> str:
        """Detailed representation."""
        return f"XWData(node={repr(self._node)}, metadata={self._metadata})"


# ==============================================================================
# ABSTRACT DATA ENGINE
# ==============================================================================

class ADataEngine(IDataEngine):
    """
    Abstract base class for data engine implementations.
    
    Provides common orchestration logic for XWDataEngine.
    Extends IDataEngine interface.
    """
    
    def __init__(self):
        """Initialize abstract engine."""
        self._serializer: Optional[Any] = None
        self._strategies: Optional[Any] = None
        self._metadata_processor: Optional[IMetadataProcessor] = None
        self._reference_resolver: Optional[IReferenceResolver] = None
        self._cache_manager: Optional[ICacheManager] = None
        self._node_factory: Optional[INodeFactory] = None
        self._config: Optional[Any] = None
    
    async def _validate_path(self, path: Union[str, Path], for_writing: bool = False) -> Path:
        """
        Validate and convert path with smart resolution.
        
        Smart path resolution:
        1. If absolute path → use as-is
        2. If relative path:
           a. Try relative to caller's script directory
           b. Fall back to current working directory
           c. Fall back to path as-is
        """
        path_obj = Path(path)
        was_relative = not path_obj.is_absolute()
        
        # Smart path resolution for relative paths
        if was_relative:
            # Try to find caller's script directory
            import inspect
            
            resolved_path = None
            
            # Get caller's frame (skip internal xwdata frames)
            for frame_info in inspect.stack():
                frame_filename = frame_info.filename
                
                # Skip internal xwdata/xwnode/xwsystem files AND Python stdlib (asyncio, pathlib, etc.)
                skip_patterns = [
                    'xwdata', 'xwnode', 'xwsystem', 'xwquery',
                    'asyncio', 'pathlib', 'inspect', 'contextlib',
                    site.getsitepackages()[0] if site.getsitepackages() else '_no_site_',
                    sys.prefix,  # Skip Python installation directory
                ]
                
                if any(x in frame_filename for x in skip_patterns):
                    continue
                
                # Found user's script - resolve relative to it
                script_dir = Path(frame_filename).parent
                candidate = script_dir / path_obj
                
                if candidate.exists() or for_writing:
                    resolved_path = candidate
                    break
            
            # Fall back to current working directory
            if resolved_path is None:
                cwd_candidate = Path.cwd() / path_obj
                if cwd_candidate.exists() or for_writing:
                    resolved_path = cwd_candidate
            
            # Use resolved path if found, otherwise use original
            if resolved_path:
                path_obj = resolved_path
        
        # Security validation - convert back to relative for validation if it was originally relative
        if self._config and hasattr(self._config, 'security'):
            if self._config.security.enable_path_validation:
                from exonware.xwsystem.security import PathValidator
                validator = PathValidator()
                
                # If path was originally relative, validate using relative form
                if was_relative:
                    # Convert to relative from cwd for validation
                    try:
                        relative_for_validation = path_obj.relative_to(Path.cwd())
                        validator.validate_path(str(relative_for_validation), for_writing=for_writing, create_dirs=True)
                    except ValueError:
                        # Can't make relative to cwd, use original relative path for validation
                        validator.validate_path(str(path), for_writing=for_writing, create_dirs=True)
                else:
                    # Was originally absolute, validate as-is
                    validator.validate_path(str(path_obj), for_writing=for_writing, create_dirs=True)
        
        return path_obj
    
    async def _validate_file_size(self, path: Path) -> None:
        """Validate file size against limits."""
        if self._config and hasattr(self._config, 'security'):
            max_size_mb = self._config.security.max_file_size_mb
            if max_size_mb:
                file_size = path.stat().st_size
                max_size = max_size_mb * 1024 * 1024
                
                if file_size > max_size:
                    from .errors import XWDataSizeLimitError
                    raise XWDataSizeLimitError(
                        f"File too large: {file_size} bytes",
                        size=file_size,
                        limit=max_size,
                        path=str(path)
                    )


# ==============================================================================
# ABSTRACT DATA NODE
# ==============================================================================

class ADataNode(IDataNode):
    """
    Abstract base class for data node implementations.
    
    Provides common functionality for XWDataNode.
    Extends IDataNode interface.
    """
    
    def __init__(self, data: Any = None, metadata: Optional[dict] = None):
        """Initialize abstract node."""
        self._data = data
        self._metadata = metadata or {}
        self._format_info: dict[str, Any] = {}
        self._references: list[Any] = []
        self._frozen = False
        self._hash_cache: Optional[int] = None
    
    def to_native(self) -> Any:
        """Convert node to native Python object."""
        return self._data
    
    @property
    def is_frozen(self) -> bool:
        """Check if node is frozen (COW active)."""
        return self._frozen
    
    @property
    def metadata(self) -> dict[str, Any]:
        """Get metadata dictionary."""
        return self._metadata.copy()
    
    @property
    def format_info(self) -> dict[str, Any]:
        """Get format information."""
        return self._format_info.copy()
    
    def __eq__(self, other) -> bool:
        """Equality check."""
        if not isinstance(other, ADataNode):
            return False
        return self.to_native() == other.to_native()
    
    def __repr__(self) -> str:
        """String representation."""
        return f"XWDataNode(data={repr(self._data)}, frozen={self._frozen})"


# ==============================================================================
# ABSTRACT FORMAT STRATEGY
# ==============================================================================

class AFormatStrategy(IFormatStrategy):
    """
    Abstract base class for format strategies.
    
    Provides common functionality for format-specific strategies.
    Extends IFormatStrategy interface.
    """
    
    def __init__(self):
        """Initialize abstract strategy."""
        self._name: str = ''
        self._extensions: list[str] = []
        self._reference_patterns: dict[str, Any] = {}
        self._type_mapping: dict[str, str] = {}
    
    @property
    def name(self) -> str:
        """Strategy name."""
        return self._name
    
    @property
    def extensions(self) -> list[str]:
        """Supported extensions."""
        return self._extensions
    
    def get_reference_patterns(self) -> dict[str, Any]:
        """Get reference patterns."""
        return self._reference_patterns
    
    def get_type_mapping(self) -> dict[str, str]:
        """Get type mapping."""
        return self._type_mapping
    
    async def extract_metadata(self, data: Any, **opts) -> dict[str, Any]:
        """Extract metadata (default implementation returns empty)."""
        return {}
    
    async def detect_references(self, data: Any, **opts) -> list[dict[str, Any]]:
        """Detect references (default implementation returns empty)."""
        return []


# ==============================================================================
# ABSTRACT METADATA PROCESSOR
# ==============================================================================

class AMetadataProcessor(IMetadataProcessor):
    """
    Abstract base class for metadata processors.
    
    Extends IMetadataProcessor interface.
    """
    
    def __init__(self):
        """Initialize abstract metadata processor."""
        self._extractors: dict[str, Any] = {}
    
    async def extract(
        self,
        data: Any,
        strategy: IFormatStrategy,
        **opts
    ) -> dict[str, Any]:
        """Extract metadata using strategy (default implementation)."""
        return await strategy.extract_metadata(data, **opts)
    
    async def apply(
        self,
        data: Any,
        metadata: dict[str, Any],
        target_format: str,
        **opts
    ) -> Any:
        """Apply metadata (default: return data unchanged)."""
        return data


# ==============================================================================
# ABSTRACT REFERENCE DETECTOR
# ==============================================================================

class AReferenceDetector(IReferenceDetector):
    """
    Abstract base class for reference detection.
    
    Extends IReferenceDetector interface.
    """
    
    def __init__(self):
        """Initialize abstract reference detector."""
        self._patterns: dict[str, Any] = {}
    
    async def detect(
        self,
        data: Any,
        strategy: IFormatStrategy,
        **opts
    ) -> list[dict[str, Any]]:
        """Detect references using strategy."""
        return await strategy.detect_references(data, **opts)


# ==============================================================================
# ABSTRACT REFERENCE RESOLVER
# ==============================================================================

class AReferenceResolver(IReferenceResolver):
    """
    Abstract base class for reference resolution.
    
    Extends IReferenceResolver interface.
    """
    
    def __init__(self):
        """Initialize abstract reference resolver."""
        self._resolution_cache: dict[str, Any] = {}
        self._resolution_stack: list[str] = []
    
    # resolve() and resolve_reference() are already abstract in IReferenceResolver interface
    # No need to redeclare - they remain abstract and must be implemented by subclasses


# ==============================================================================
# ABSTRACT CACHE MANAGER
# ==============================================================================

class ACacheManager(ICacheManager):
    """
    Abstract base class for cache management.
    
    Extends ICacheManager interface.
    """
    
    def __init__(self):
        """Initialize abstract cache manager."""
        self._cache: dict[str, Any] = {}
        self._stats = {'hits': 0, 'misses': 0, 'sets': 0}
    
    async def get(self, key: str) -> Optional[Any]:
        """Get from cache (basic implementation)."""
        if key in self._cache:
            self._stats['hits'] += 1
            return self._cache[key]
        self._stats['misses'] += 1
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set in cache (basic implementation)."""
        self._cache[key] = value
        self._stats['sets'] += 1
    
    async def invalidate(self, key: str) -> None:
        """Invalidate cache entry."""
        if key in self._cache:
            del self._cache[key]
    
    async def clear(self) -> None:
        """Clear all cache."""
        self._cache.clear()
    
    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total = self._stats['hits'] + self._stats['misses']
        hit_rate = (self._stats['hits'] / total * 100) if total > 0 else 0
        
        return {
            'hits': self._stats['hits'],
            'misses': self._stats['misses'],
            'sets': self._stats['sets'],
            'hit_rate': hit_rate,
            'size': len(self._cache)
        }


# ==============================================================================
# ABSTRACT NODE FACTORY
# ==============================================================================

class ANodeFactory(INodeFactory):
    """
    Abstract base class for node factory.
    
    Extends INodeFactory interface.
    """
    
    def __init__(self):
        """Initialize abstract factory."""
        self._pool: list[Any] = []
        self._config: Optional[Any] = None


# ==============================================================================
# ABSTRACT XWDATA SERIALIZER
# ==============================================================================

class AXWDataSerializer(IXWDataSerializer):
    """
    Abstract base class for xwdata serializers.
    
    Extends IXWDataSerializer interface.
    Can optionally extend xwsystem's ASerialization for base functionality.
    """
    
    def __init__(self):
        """Initialize abstract serializer."""
        self._name: str = ''
        self._extensions: list[str] = []
        self._base_serializer: Optional[Any] = None
    
    @property
    def name(self) -> str:
        """Serializer name."""
        return self._name
    
    @property
    def extensions(self) -> list[str]:
        """Supported extensions."""
        return self._extensions
    
    def detect(self, content: Union[str, bytes]) -> float:
        """Default detection returns 0.0."""
        return 0.0


# ==============================================================================
# EXPORTS
# ==============================================================================

__all__ = [
    # Abstract classes
    'AData',
    'ADataEngine',
    'ADataNode',
    'AFormatStrategy',
    'AMetadataProcessor',
    'AReferenceDetector',
    'AReferenceResolver',
    'ACacheManager',
    'ANodeFactory',
    'AXWDataSerializer',
]

