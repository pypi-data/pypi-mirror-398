#!/usr/bin/env python3
"""
#exonware/xwdata/src/exonware/xwdata/facade.py

XWData Facade - Main User API

This module provides the primary user-facing API with:
- Multi-type __init__ (handles dict/list/path/XWData/merge)
- Rich fluent API with method chaining
- Async operations throughout
- COW semantics for immutability
- Engine-driven orchestration

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 26-Oct-2025
"""

import asyncio
from typing import Any, Optional, Union, AsyncIterator
from pathlib import Path
from exonware.xwsystem import get_logger, async_safe_read_text, async_safe_write_text

from .base import AData
from .config import XWDataConfig
from .data.engine import XWDataEngine
from .data.node import XWDataNode
from .defs import DataFormat, MergeStrategy
from .errors import XWDataTypeError, XWDataError

logger = get_logger(__name__)


class XWData(AData):
    """
    XWData - Universal data manipulation facade.
    
    Features:
    - Multi-type constructor (dict/list/path/XWData/list of sources)
    - Automatic format detection and conversion
    - COW semantics for safe mutations
    - Async operations throughout
    - Fluent chainable API
    - Engine-driven orchestration
    - xwsystem serialization integration (reuse!)
    - xwnode navigation capabilities
    
    Examples:
        # From native data
        data = XWData({'name': 'Alice', 'age': 30})
        
        # From file
        data = await XWData.load('config.json')
        
        # From multiple sources (merge)
        data = XWData([
            {'base': 'config'},
            'overrides.yaml',
            existing_data
        ], merge_strategy='deep')
        
        # Fluent API
        data = await XWData.load('config.json')
        await data.set('api.timeout', 30)
        await data.save('config.yaml')  # JSON → YAML!
    """
    
    def __init__(
        self,
        data: Union[
            XWDataNode,                          # Direct node
            dict, list,                           # Native Python
            str, Path,                            # File path
            'XWData',                             # Copy/merge from another
            list[Union[dict, str, Path, 'XWData']] # Multiple sources to merge
        ],
        metadata: Optional[dict] = None,
        config: Optional[XWDataConfig] = None,
        merge_strategy: Union[str, MergeStrategy] = 'deep',
        **opts
    ):
        """
        Universal constructor handling multiple input types intelligently.
        
        This is the brilliant multi-type init pattern that makes XWData
        incredibly flexible and easy to use.
        
        Args:
            data: Data in various forms (see type hints)
            metadata: Optional metadata to attach
            config: Optional configuration
            merge_strategy: Strategy for merging multiple sources
            **opts: Additional options
        """
        super().__init__()
        self._config = config or XWDataConfig.default()
        self._engine = XWDataEngine(self._config)
        
        # Multi-type handling - the magic happens here!
        if isinstance(data, list) and data and all(
            isinstance(item, (dict, list, str, Path, XWData)) for item in data
        ):
            # Multiple sources - MERGE them!
            logger.debug(f"Merging {len(data)} sources with strategy: {merge_strategy}")
            self._node = self._sync_merge_sources(data, merge_strategy)
        
        elif isinstance(data, XWDataNode):
            # Already a node - use directly
            self._node = data
        
        elif isinstance(data, XWData):
            # Copy from another XWData
            self._node = data._node.copy() if self._config.cow.copy_on_init else data._node
            if metadata and self._node:
                for key, value in metadata.items():
                    self._node.set_metadata(key, value)
        
        elif isinstance(data, (dict, list)):
            # Native Python data - wrap it (sync wrapper)
            self._node = self._sync_create_from_native(data, metadata)
        
        elif isinstance(data, (str, Path)):
            # File path - load it (sync wrapper)
            self._node = self._sync_load_file(str(data))
            if metadata and self._node:
                for key, value in metadata.items():
                    self._node.set_metadata(key, value)
        
        else:
            raise XWDataTypeError(
                f"Cannot create XWData from type: {type(data).__name__}",
                expected_type="XWDataNode, dict, list, str, Path, XWData, or list[...]",
                actual_type=type(data).__name__
            )
        
        # Store metadata
        if self._node:
            self._metadata = self._node.metadata
        else:
            self._metadata = {}
    
    def _sync_load_file(self, path: str) -> XWDataNode:
        """
        Sync wrapper for loading file in __init__.
        
        Args:
            path: File path to load
            
        Returns:
            XWDataNode
        """
        # Use new event loop pattern to avoid conflicts
        new_loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(new_loop)
            return new_loop.run_until_complete(self._engine.load(path))
        finally:
            new_loop.close()
            asyncio.set_event_loop(None)
    
    def _sync_create_from_native(self, data: Any, metadata: Optional[dict] = None) -> XWDataNode:
        """
        Sync wrapper for creating from native data in __init__.
        
        Args:
            data: Native data
            metadata: Optional metadata
            
        Returns:
            XWDataNode
        """
        # Use new event loop pattern to avoid conflicts
        new_loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(new_loop)
            return new_loop.run_until_complete(self._engine.create_node_from_native(data, metadata))
        finally:
            new_loop.close()
            asyncio.set_event_loop(None)
    
    def _sync_merge_sources(
        self,
        sources: list[Union[dict, list, str, Path, 'XWData']],
        strategy: Union[str, MergeStrategy]
    ) -> XWDataNode:
        """Sync wrapper for merging sources in __init__."""
        # Use new event loop pattern to avoid conflicts
        new_loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(new_loop)
            return new_loop.run_until_complete(self._merge_multiple_sources(sources, strategy))
        finally:
            new_loop.close()
            asyncio.set_event_loop(None)
    
    async def _merge_multiple_sources(
        self,
        sources: list[Union[dict, list, str, Path, 'XWData']],
        strategy: Union[str, MergeStrategy]
    ) -> XWDataNode:
        """Merge multiple data sources into one node."""
        nodes = []
        
        # Convert all sources to nodes
        for source in sources:
            if isinstance(source, XWData):
                nodes.append(source._node)
            elif isinstance(source, XWDataNode):
                nodes.append(source)
            elif isinstance(source, (dict, list)):
                node = await self._engine.create_node_from_native(source)
                nodes.append(node)
            elif isinstance(source, (str, Path)):
                # File paths in merge - load them
                node = await self._engine.load(str(source))
                nodes.append(node)
        
        # Engine merges all nodes
        return await self._engine.merge_nodes(nodes, strategy)
    
    # ==========================================================================
    # FACTORY METHODS
    # ==========================================================================
    
    @classmethod
    async def load(
        cls,
        path: Union[str, Path],
        format_hint: Optional[Union[str, DataFormat]] = None,
        config: Optional[XWDataConfig] = None,
        **opts
    ) -> 'XWData':
        """
        Load data from file (async).
        
        Args:
            path: File path
            format_hint: Optional format hint
            config: Optional configuration
            **opts: Additional options
            
        Returns:
            XWData instance
        """
        cfg = config or XWDataConfig.default()
        engine = XWDataEngine(cfg)
        
        # Convert format if enum
        format_str = format_hint.name.lower() if isinstance(format_hint, DataFormat) else format_hint
        
        node = await engine.load(path, format_hint=format_str, **opts)
        instance = cls.__new__(cls)
        instance._config = cfg
        instance._engine = engine
        instance._node = node
        instance._metadata = node.metadata
        
        return instance
    
    # ==========================================================================
    # V8: PARTIAL ACCESS API (For Large Files)
    # ==========================================================================
    
    @classmethod
    async def get_at(
        cls,
        path: Union[str, Path],
        json_path: str,
        config: Optional[XWDataConfig] = None,
        **opts
    ) -> Any:
        """
        Get value at specific path without loading entire file (V8).
        
        Format-agnostic! Supports:
        - JSON: JSON Pointer (e.g., '/users/0/name')
        - YAML: Dot notation (e.g., 'users.0.name')
        - XML: XPath (e.g., '//users/user[1]/name')
        - TOML: Dot notation (e.g., 'users.0.name')
        - CSV: Row/column access
        - BSON: JSON Pointer
        - +24 other formats via AutoSerializer
        
        Args:
            path: File path
            json_path: Path expression (format-specific syntax)
            config: Optional configuration
            **opts: Additional options
        
        Returns:
            Value at specified path
        
        Example:
            >>> # Works for any format!
            >>> name = await XWData.get_at('huge.json', 'users.0.name')
            >>> name = await XWData.get_at('huge.yaml', 'users.0.name')
            >>> name = await XWData.get_at('huge.xml', '//users/user[1]/name')
        """
        cfg = config or XWDataConfig.default()
        
        # PERFORMANCE-FIRST: Get format-specific serializer
        from .utils.format_helpers import get_serializer_for_path
        serializer = get_serializer_for_path(path, fast_path=True)
        
        # Read file content
        content = await async_safe_read_text(str(path))
        
        # Use format-specific partial access
        return serializer.get_at(content, json_path)
    
    @classmethod
    async def set_at(
        cls,
        path: Union[str, Path],
        json_path: str,
        value: Any,
        config: Optional[XWDataConfig] = None,
        **opts
    ) -> None:
        """
        Set value at specific path without loading entire file (V8).
        
        Format-agnostic! Supports:
        - JSON: JSON Patch (RFC 6902)
        - YAML: Dot notation updates
        - XML: XPath updates
        - TOML: Dot notation updates
        - CSV: Row/column updates
        - BSON: JSON Patch
        - +24 other formats via AutoSerializer
        
        Args:
            path: File path
            json_path: Path expression (format-specific syntax)
            value: New value to set
            config: Optional configuration
            **opts: Additional options
        
        Example:
            >>> # Works for any format!
            >>> await XWData.set_at('huge.json', 'users.0.age', 31)
            >>> await XWData.set_at('huge.yaml', 'users.0.age', 31)
            >>> await XWData.set_at('huge.xml', '//users/user[1]/age', 31)
        """
        cfg = config or XWDataConfig.default()
        
        # PERFORMANCE-FIRST: Get format-specific serializer
        from .utils.format_helpers import get_serializer_for_path
        serializer = get_serializer_for_path(path, fast_path=True)
        
        # Read file content
        content = await async_safe_read_text(str(path))
        
        # Use format-specific partial access
        updated = serializer.set_at(content, json_path, value)
        
        # Atomic write
        await async_safe_write_text(str(path), updated)
    
    # ==========================================================================
    # V8: TYPED LOADING
    # ==========================================================================
    
    @classmethod
    async def load_typed(
        cls,
        path: Union[str, Path],
        type_: type,
        config: Optional[XWDataConfig] = None,
        **opts
    ) -> Any:
        """
        Load and validate to specific type (V8).
        
        Format-agnostic! Works with:
        - JSON, YAML, TOML, XML, BSON (full support)
        - +24 other formats via AutoSerializer
        
        Args:
            path: File path
            type_: Target type (dataclass, NamedTuple, etc.)
            config: Optional configuration
            **opts: Additional options
        
        Returns:
            Instance of specified type
        
        Example:
            >>> @dataclass
            >>> class Config:
            >>>     api_key: str
            >>>     timeout: int
            >>> 
            >>> # Works with any format!
            >>> config = await XWData.load_typed('config.json', Config)
            >>> config = await XWData.load_typed('config.yaml', Config)
            >>> config = await XWData.load_typed('config.toml', Config)
        """
        cfg = config or XWDataConfig.default()
        
        # PERFORMANCE-FIRST: Get format-specific serializer
        from .utils.format_helpers import get_serializer_for_path
        serializer = get_serializer_for_path(path, fast_path=True)
        
        # Read file content
        content = await async_safe_read_text(str(path))
        
        # Use format-specific typed loading
        return serializer.loads_typed(content, type_)
    
    # ==========================================================================
    # V8: CANONICAL HASHING
    # ==========================================================================
    
    def hash(
        self,
        algorithm: str = 'xxh3'
    ) -> str:
        """
        Generate canonical hash (same data = same hash, regardless of key order) (V8).
        
        Format-agnostic! Works with all formats that support canonical serialization:
        - JSON: Sorted keys, deterministic
        - YAML: Sorted keys, deterministic
        - XML: C14N canonicalization
        - TOML: Sorted keys, deterministic
        - BSON: Standard encoding
        - MessagePack: Sorted keys
        - +20 other formats
        
        Perfect for:
        - Cache keys (no false misses from key order)
        - ETags (HTTP caching)
        - Content addressing
        - Deduplication
        
        Args:
            algorithm: Hash algorithm ('xxh3', 'sha256', 'md5', etc.)
        
        Returns:
            Canonical hash string
        
        Example:
            >>> # Works regardless of source format!
            >>> json_data = XWData({'name': 'Alice', 'age': 30})
            >>> yaml_data = XWData({'age': 30, 'name': 'Alice'})
            >>> hash1 = json_data.hash()
            >>> hash2 = yaml_data.hash()
            >>> assert hash1 == hash2  # Same hash despite different order!
        """
        # PERFORMANCE-FIRST: Use format-specific canonical hashing
        # Get format from metadata (if available)
        format_name = self._metadata.get('format', 'JSON')
        
        from .utils.format_helpers import get_serializer_for_format, is_core_format
        
        # Fast path for core formats
        if is_core_format(format_name):
            serializer = get_serializer_for_format(format_name, fast_path=True)
        else:
            # Fallback to JSON serializer for non-core formats
            from exonware.xwsystem.serialization import JsonSerializer
            serializer = JsonSerializer()
        
        native = self.to_native()
        return serializer.hash_stable(native, algorithm)
    
    @classmethod
    def from_native(
        cls,
        data: Union[dict, list],
        metadata: Optional[dict] = None,
        config: Optional[XWDataConfig] = None,
        **opts
    ) -> 'XWData':
        """
        Create from native Python data (sync).
        
        Uses direct node creation to avoid async context issues.
        
        Args:
            data: Native Python data
            metadata: Optional metadata
            config: Optional configuration
            **opts: Additional options
            
        Returns:
            XWData instance
        """
        cfg = config or XWDataConfig.default()
        engine = XWDataEngine(cfg)
        
        # Create node directly (sync) - avoid async
        from .data.node import XWDataNode
        node = XWDataNode(data=data, metadata=metadata or {})
        
        # Create instance
        instance = cls.__new__(cls)
        instance._config = cfg
        instance._engine = engine
        instance._node = node
        instance._metadata = node.metadata if node else {}
        
        return instance
    
    @classmethod
    async def parse(
        cls,
        content: Union[str, bytes],
        format: Union[str, DataFormat],
        config: Optional[XWDataConfig] = None,
        **opts
    ) -> 'XWData':
        """
        Parse content with specified format (async).
        
        Args:
            content: Content to parse
            format: Format name
            config: Optional configuration
            **opts: Parse options
            
        Returns:
            XWData instance
        """
        cfg = config or XWDataConfig.default()
        engine = XWDataEngine(cfg)
        
        # Convert format if enum
        format_str = format.name.lower() if isinstance(format, DataFormat) else format
        
        node = await engine.parse(content, format_str, **opts)
        instance = cls.__new__(cls)
        instance._config = cfg
        instance._engine = engine
        instance._node = node
        instance._metadata = node.metadata
        
        return instance
    
    # ==========================================================================
    # NAVIGATION
    # ==========================================================================
    
    async def get(self, path: str, default: Any = None) -> Any:
        """
        Get value at path.
        
        Args:
            path: Dot-separated path
            default: Default value if path doesn't exist
            
        Returns:
            Value at path or default
        """
        # If this XWData was loaded in lazy file mode, use engine-level atomic
        # access to avoid fully materializing huge files.
        if self._metadata.get('lazy_mode') == 'file':
            return await self._engine.lazy_get_from_file(self._node, path, default)
        return self._node.get_value_at_path(path, default)
    
    async def exists(self, path: str) -> bool:
        """
        Check if path exists.
        
        Args:
            path: Dot-separated path
            
        Returns:
            True if path exists
        """
        return self._node.path_exists(path)
    
    def to_native(self) -> Any:
        """Get native Python data."""
        return self._node.to_native()

    async def get_page(
        self,
        page_number: int,
        page_size: int
    ) -> list['XWData']:
        """
        Retrieve a page of records from this XWData.

        Behaviour:
        - For large, file-backed lazy datasets (JSONL/NDJSON), this uses the
          engine's file-level paging to avoid loading the full file.
        - For in-memory list data, this falls back to simple slicing.
        """
        # File-backed lazy mode: delegate to engine paging.
        if self._metadata.get('lazy_mode') == 'file':
            nodes = await self._engine.get_page_from_file(
                self._node,
                page_number=page_number,
                page_size=page_size
            )
            results: list[XWData] = []
            for node in nodes:
                instance = XWData.__new__(XWData)
                instance._config = self._config
                instance._engine = self._engine
                instance._node = node
                instance._metadata = node.metadata
                results.append(instance)
            return results

        # In-memory fallback: page over top-level list if available.
        data = self._node.to_native()
        if isinstance(data, list):
            start = max((page_number - 1) * page_size, 0)
            end = start + page_size
            slice_data = data[start:end]
            results: list[XWData] = []
            for item in slice_data:
                node = await self._engine.create_node_from_native(
                    item,
                    metadata=self._metadata.copy()
                )
                instance = XWData.__new__(XWData)
                instance._config = self._config
                instance._engine = self._engine
                instance._node = node
                instance._metadata = node.metadata
                results.append(instance)
            return results

        raise TypeError("Paging is only supported for list-like data")
    
    # ==========================================================================
    # MUTATION (Copy-on-Write)
    # ==========================================================================
    
    async def set(self, path: str, value: Any) -> 'XWData':
        """
        Set value at path (returns new instance with COW).
        
        Args:
            path: Dot-separated path
            value: Value to set
            
        Returns:
            New XWData instance
        """
        # For lazy file-backed data, prefer atomic path update when possible.
        if self._metadata.get('lazy_mode') == 'file':
            new_node = await self._engine.lazy_set_in_file(self._node, path, value)
        else:
            new_node = self._node.set_value_at_path(path, value)
        
        # Create new XWData instance
        instance = XWData.__new__(XWData)
        instance._config = self._config
        instance._engine = self._engine
        instance._node = new_node
        instance._metadata = new_node.metadata
        
        return instance
    
    async def delete(self, path: str) -> 'XWData':
        """
        Delete value at path (returns new instance with COW).
        
        Args:
            path: Dot-separated path
            
        Returns:
            New XWData instance
        """
        new_node = self._node.delete_at_path(path)
        
        # Create new XWData instance
        instance = XWData.__new__(XWData)
        instance._config = self._config
        instance._engine = self._engine
        instance._node = new_node
        instance._metadata = new_node.metadata
        
        return instance
    
    # ==========================================================================
    # OPERATIONS
    # ==========================================================================
    
    async def merge(
        self,
        other: 'XWData',
        strategy: Union[str, MergeStrategy] = 'deep'
    ) -> 'XWData':
        """
        Merge with another XWData instance.
        
        Args:
            other: Other XWData to merge
            strategy: Merge strategy
            
        Returns:
            New merged XWData instance
        """
        merged_node = await self._engine.merge_nodes(
            [self._node, other._node],
            strategy
        )
        
        instance = XWData.__new__(XWData)
        instance._config = self._config
        instance._engine = self._engine
        instance._node = merged_node
        instance._metadata = merged_node.metadata
        
        return instance
    
    async def transform(self, transformer: callable) -> 'XWData':
        """
        Transform data using function.
        
        Args:
            transformer: Transformation function
            
        Returns:
            New XWData instance with transformed data
        """
        transformed_data = transformer(self._node.to_native())
        transformed_node = await self._engine.create_node_from_native(transformed_data)
        
        instance = XWData.__new__(XWData)
        instance._config = self._config
        instance._engine = self._engine
        instance._node = transformed_node
        instance._metadata = transformed_node.metadata
        
        return instance
    
    # ==========================================================================
    # SERIALIZATION
    # ==========================================================================
    
    async def serialize(
        self,
        format: Optional[Union[str, DataFormat]] = None,
        **opts
    ) -> Union[str, bytes]:
        """
        Serialize to specified format.
        
        Format priority:
        1. format parameter (explicit override)
        2. set_format (user override via set_format())
        3. detected_format (original format)
        4. JSON (default)
        
        Args:
            format: Optional target format (uses active format if not specified)
            **opts: Format-specific options
            
        Returns:
            Serialized content
        """
        # Determine format: explicit > active format
        if format:
            format_str = format.name.lower() if isinstance(format, DataFormat) else format
        else:
            format_str = self.get_active_format()
        
        # Get serializer from xwsystem
        serializer = self._engine._ensure_serializer()
        native_data = self._node.to_native()
        
        # Serialize via xwsystem (this is sync, no need for executor)
        return serializer.detect_and_serialize(native_data, format_hint=format_str)
    
    def to_format(self, format: Optional[Union[str, DataFormat]] = None, **opts) -> Union[str, bytes]:
        """
        Synchronously serialize to specified format.
        
        Convenient wrapper around serialize() for synchronous use cases.
        Fully reuses xwsystem's AutoSerializer for format I/O.
        
        Args:
            format: Optional target format (uses active format if not specified)
            **opts: Format-specific options
            
        Returns:
            Serialized content (str for text formats, bytes for binary)
            
        Example:
            >>> data = XWData({'name': 'Alice'})
            >>> json_str = data.to_format("json")
            >>> xml_str = data.to_format("xml")
        """
        # Sync wrapper for serialize() using asyncio.run()
        new_loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(new_loop)
            return new_loop.run_until_complete(self.serialize(format, **opts))
        finally:
            new_loop.close()
            asyncio.set_event_loop(None)
    
    async def save(
        self,
        destinations: Union[str, Path, list[Union[str, Path]], list[tuple], dict[str, str]],
        format: Optional[Union[str, DataFormat]] = None,
        overwrite: bool = True,
        **opts
    ) -> 'XWData':
        """
        Save to single or multiple destinations with different formats.
        
        Format priority:
        1. format parameter (explicit override)
        2. set_format (user override via set_format())
        3. detected_format (original format)
        4. Extension from path
        
        Args:
            destinations: Can be:
                - str/Path: Single file (classic behavior)
                - list[str/Path]: Multiple files, auto-detect formats from extensions
                - list[tuple[str/Path, str]]: Files with explicit formats [(path, format), ...]
                - dict[str, str]: {path: format} mapping
            format: Optional format override (for single destination)
            overwrite: Whether to overwrite existing files
            **opts: Serialization options
            
        Returns:
            Self for chaining
            
        Examples:
            >>> # Single file
            >>> await data.save("config.json")
            >>> 
            >>> # Multiple files, auto-detect formats
            >>> await data.save(["config.json", "config.xml", "backup.yaml"])
            >>> 
            >>> # Multiple files with explicit formats
            >>> await data.save([("config.json", "json"), ("backup.xml", "xml")])
            >>> 
            >>> # Dictionary format
            >>> await data.save({"config.json": "json", "backup.yaml": "yaml"})
        """
        # Handle single destination (classic behavior)
        if isinstance(destinations, (str, Path)):
            path_obj = Path(destinations)
            
            # Check if file exists
            if not overwrite and path_obj.exists():
                from .errors import XWDataIOError
                raise XWDataIOError(
                    f"File already exists: {path_obj}",
                    path=str(path_obj),
                    suggestion="Set overwrite=True to overwrite existing file"
                )
            
            # Determine format priority:
            # 1. Explicit format parameter
            # 2. File extension (let engine handle this)
            # 3. Active format (set_format or detected_format)
            if format:
                format_str = format.name.lower() if isinstance(format, DataFormat) else format
            else:
                # Check if file has extension - if so, let engine auto-detect from extension
                # Otherwise use active format
                if path_obj.suffix:
                    format_str = None  # Let engine detect from extension
                else:
                    format_str = self.get_active_format()
            
            # Save via engine
            await self._engine.save(self._node, path_obj, format=format_str, **opts)
            
            return self
        
        # Handle multiple destinations
        dest_list = []
        
        if isinstance(destinations, dict):
            # dict format: {path: format}
            dest_list = [(path, fmt) for path, fmt in destinations.items()]
        
        elif isinstance(destinations, list):
            for dest in destinations:
                if isinstance(dest, tuple):
                    # Explicit (path, format) tuple
                    dest_list.append(dest)
                else:
                    # Auto-detect format from extension
                    path_obj = Path(dest)
                    ext_format = path_obj.suffix.lstrip('.').upper()
                    dest_list.append((dest, ext_format))
        
        # Save to all destinations
        for path, fmt in dest_list:
            path_obj = Path(path)
            
            # Check overwrite
            if not overwrite and path_obj.exists():
                logger.warning(f"Skipping existing file: {path_obj}")
                continue
            
            # Save
            await self._engine.save(self._node, path_obj, format=fmt, **opts)
            logger.info(f"Saved to {path_obj} ({fmt})")
        
        return self
    
    # ==========================================================================
    # STREAMING
    # ==========================================================================
    
    @classmethod
    async def stream_load(
        cls,
        path: Union[str, Path],
        chunk_size: int = 8192,
        config: Optional[XWDataConfig] = None,
        **opts
    ) -> AsyncIterator['XWData']:
        """
        Stream load large files (async generator).
        
        Args:
            path: File path
            chunk_size: Chunk size
            config: Optional configuration
            **opts: Additional options
            
        Yields:
            XWData instances for each chunk/document
        """
        cfg = config or XWDataConfig.default()
        engine = XWDataEngine(cfg)
        
        async for node in engine.stream_load(path, chunk_size, **opts):
            instance = cls.__new__(cls)
            instance._config = cfg
            instance._engine = engine
            instance._node = node
            instance._metadata = node.metadata
            yield instance
    
    async def stream_save(
        self,
        path: Union[str, Path],
        format: Optional[Union[str, DataFormat]] = None,
        chunk_size: int = 8192,
        **opts
    ) -> 'XWData':
        """
        Stream save data to file (for large datasets).
        
        Args:
            path: Output file path
            format: Optional format override
            chunk_size: Chunk size for streaming
            **opts: Format-specific options
            
        Returns:
            Self for chaining
            
        Example:
            >>> data = await XWData.load('large_file.json')
            >>> await data.stream_save('output.jsonl', chunk_size=1024)
        """
        path_obj = Path(path)
        
        # Determine format
        if format:
            format_str = format.name.lower() if isinstance(format, DataFormat) else format
        else:
            format_str = self.get_active_format()
        
        # Stream save via engine
        await self._engine.stream_save(self._node, path_obj, format=format_str, chunk_size=chunk_size, **opts)
        
        return self
    
    # ==========================================================================
    # FILE I/O ALIASES (from MIGRAT)
    # ==========================================================================
    
    def to_file(
        self,
        path: Union[str, Path],
        format: Optional[Union[str, DataFormat]] = None,
        overwrite: bool = True,
        **opts
    ) -> 'XWData':
        """
        Save to file (alias for save) - synchronous wrapper.
        
        Args:
            path: Output file path
            format: Optional format override
            overwrite: Whether to overwrite existing files
            **opts: Format-specific options
            
        Returns:
            Self for chaining
        """
        import asyncio
        
        # Create and use a new event loop to avoid conflicts
        new_loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(new_loop)
            result = new_loop.run_until_complete(self.save(path, format, overwrite, **opts))
            return result
        finally:
            new_loop.close()
            asyncio.set_event_loop(None)
    
    @classmethod
    async def from_file_async(
        cls,
        path: Union[str, Path],
        format: Optional[Union[str, DataFormat]] = None,
        config: Optional['XWDataConfig'] = None,
        **opts
    ) -> 'XWData':
        """
        Load from file (async version, alias for load).
        
        Args:
            path: File path
            format: Optional format hint (auto-detected from extension if not provided)
            config: Optional configuration
            **opts: Format-specific options
            
        Returns:
            XWData instance
        """
        return await cls.load(path, format, config, **opts)
    
    @classmethod
    def from_file(
        cls,
        path: Union[str, Path],
        format: Optional[Union[str, DataFormat]] = None,
        config: Optional['XWDataConfig'] = None,
        **opts
    ) -> 'XWData':
        """
        Synchronously load from file (auto-detects format from extension).
        
        Args:
            path: File path
            format: Optional format hint (auto-detected from extension if not provided)
            config: Optional configuration
            **opts: Format-specific options
            
        Returns:
            XWData instance
            
        Example:
            >>> data = XWData.from_file("config.json")  # Auto-detects JSON from extension
            >>> data = XWData.from_file("data.xml", format="xml")  # Explicit format
        """
        # Sync wrapper for load()
        new_loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(new_loop)
            return new_loop.run_until_complete(cls.load(path, format, config, **opts))
        finally:
            new_loop.close()
            asyncio.set_event_loop(None)
    
    @classmethod
    def from_format(
        cls,
        content: Union[str, bytes],
        format: Union[str, DataFormat],
        config: Optional['XWDataConfig'] = None,
        **opts
    ) -> 'XWData':
        """
        Synchronously create from formatted content.
        
        Args:
            content: Content to parse (str or bytes)
            format: Format name (e.g., "json", "xml", "yaml")
            config: Optional configuration
            **opts: Format-specific options
            
        Returns:
            XWData instance
            
        Example:
            >>> json_str = '{"name": "Alice", "age": 30}'
            >>> data = XWData.from_format(json_str, "json")
            >>> xml_str = '<root><name>Alice</name></root>'
            >>> data = XWData.from_format(xml_str, "xml")
        """
        # Sync wrapper for parse()
        new_loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(new_loop)
            return new_loop.run_until_complete(cls.parse(content, format, config, **opts))
        finally:
            new_loop.close()
            asyncio.set_event_loop(None)
    
    # ==========================================================================
    # NAVIGATION & BATCH OPERATIONS (delegated to XWNode)
    # ==========================================================================
    
    def select(self, path: str) -> 'XWData':
        """
        Select sub-data at path (zero-copy view).
        
        Returns a new XWData wrapping the value at the specified path.
        
        Args:
            path: Dot-separated path
            
        Returns:
            XWData wrapping the value at path
            
        Example:
            >>> data = await XWData.load('users.json')
            >>> user = data.select('users.0')
            >>> print(user.get('name'))  # 'Alice'
        """
        # Navigate to get the value synchronously
        value = self._node.get_value_at_path(path, default=None)
        
        # Create new XWData wrapping this value
        instance = XWData.__new__(XWData)
        instance._config = self._config
        instance._engine = self._engine
        instance._node = self._sync_create_from_native(value, {'selected_path': path})
        instance._metadata = instance._node.metadata
        
        return instance
    
    def select_many(self, paths: list[str]) -> dict[str, 'XWData']:
        """
        Select multiple paths efficiently.
        
        Args:
            paths: List of paths
            
        Returns:
            Dictionary mapping paths to XWData instances
            
        Example:
            >>> data = await XWData.load('config.json')
            >>> results = data.select_many(['api.url', 'api.timeout'])
        """
        return {path: self.select(path) for path in paths}
    
    async def set_many(self, updates: dict[str, Any]) -> 'XWData':
        """
        Set multiple values efficiently.
        
        Args:
            updates: Dictionary mapping paths to values
            
        Returns:
            XWData with all updates applied
            
        Example:
            >>> data = await XWData.load('config.json')
            >>> updated = await data.set_many({'api.url': 'https://new.url', 'api.timeout': 60})
        """
        current = self
        for path, value in updates.items():
            current = await current.set(path, value)
        return current
    
    # ==========================================================================
    # COMPARISON & PATCHING OPERATIONS (from MIGRAT)
    # ==========================================================================
    
    def diff(self, other: 'XWData') -> dict[str, Any]:
        """
        Compare with another XWData instance.
        
        Args:
            other: Other XWData to compare
            
        Returns:
            Dictionary describing differences
            
        Example:
            >>> data1 = await XWData.from_native({'name': 'Alice', 'age': 30})
            >>> data2 = await XWData.from_native({'name': 'Bob', 'age': 30})
            >>> diffs = data1.diff(data2)
            >>> print(diffs)  # {'name': {'old': 'Alice', 'new': 'Bob'}}
        """
        self_data = self._node.to_native()
        other_data = other._node.to_native()
        
        def _diff_recursive(obj1, obj2, path=""):
            """Recursively compare two objects."""
            differences = {}
            
            if type(obj1) != type(obj2):
                differences[path or "root"] = {"old": obj1, "new": obj2}
                return differences
            
            if isinstance(obj1, dict):
                all_keys = set(obj1.keys()) | set(obj2.keys())
                for key in all_keys:
                    new_path = f"{path}.{key}" if path else key
                    if key not in obj1:
                        differences[new_path] = {"old": None, "new": obj2[key]}
                    elif key not in obj2:
                        differences[new_path] = {"old": obj1[key], "new": None}
                    elif obj1[key] != obj2[key]:
                        nested_diff = _diff_recursive(obj1[key], obj2[key], new_path)
                        differences.update(nested_diff)
            
            elif isinstance(obj1, list):
                max_len = max(len(obj1), len(obj2))
                for i in range(max_len):
                    new_path = f"{path}.{i}" if path else str(i)
                    if i >= len(obj1):
                        differences[new_path] = {"old": None, "new": obj2[i]}
                    elif i >= len(obj2):
                        differences[new_path] = {"old": obj1[i], "new": None}
                    elif obj1[i] != obj2[i]:
                        nested_diff = _diff_recursive(obj1[i], obj2[i], new_path)
                        differences.update(nested_diff)
            
            elif obj1 != obj2:
                differences[path or "root"] = {"old": obj1, "new": obj2}
            
            return differences
        
        return _diff_recursive(self_data, other_data)
    
    async def patch(self, operations: list[dict[str, Any]]) -> 'XWData':
        """
        Apply JSON patch operations.
        
        Args:
            operations: List of patch operations
                Each operation should have: {"op": "...", "path": "...", "value": ...}
                Supported ops: "add", "remove", "replace", "move", "copy"
            
        Returns:
            New XWData instance with patches applied
            
        Example:
            >>> data = await XWData.from_native({'name': 'Alice', 'age': 30})
            >>> patched = await data.patch([
            ...     {"op": "replace", "path": "name", "value": "Bob"},
            ...     {"op": "add", "path": "email", "value": "bob@example.com"}
            ... ])
        """
        current = self
        
        for operation in operations:
            op = operation.get("op", "").lower()
            path = operation.get("path", "")
            value = operation.get("value")
            
            if op == "add" or op == "replace":
                current = await current.set(path, value)
            elif op == "remove":
                current = await current.delete(path)
            elif op == "move":
                from_path = operation.get("from", "")
                value_to_move = await current.get(from_path)
                current = await current.delete(from_path)
                current = await current.set(path, value_to_move)
            elif op == "copy":
                from_path = operation.get("from", "")
                value_to_copy = await current.get(from_path)
                current = await current.set(path, value_to_copy)
        
        return current
    
    def native(self, copy: bool = False) -> Any:
        """
        Get native Python data (alias for to_native with copy option).
        
        Args:
            copy: Whether to return a deep copy
            
        Returns:
            Native Python data
            
        Example:
            >>> data = await XWData.load('users.json')
            >>> native = data.native(copy=True)  # Deep copy
        """
        data = self.to_native()
        
        if copy:
            import copy as copy_module
            return copy_module.deepcopy(data)
        
        return data
    
    # ==========================================================================
    # UTILITY METHODS
    # ==========================================================================
    
    def __eq__(self, other: Any) -> bool:
        """Equality check using structural hashing."""
        if not isinstance(other, XWData):
            return False
        
        if self._config.performance.enable_structural_hashing:
            return self._node.structural_hash == other._node.structural_hash
        else:
            return self._node.to_native() == other._node.to_native()
    
    # ==========================================================================
    # DICTIONARY-LIKE ACCESS (Subscriptable)
    # ==========================================================================
    
    def __getitem__(self, key: Union[str, int, slice]) -> Any:
        """
        Get value using bracket notation with path support.
        
        Delegates to XWNode for optimal performance, reusing XWNode's indexing capabilities.
        
        Supports:
        - Integer indices: data[0] for list access
        - Simple keys: data["users"]
        - Dotted paths: data["users.0.full_name"]
        - Array indices: data["users.0"] or data["items.5"]
        - Slices: data[0:5] for list slicing
        
        Args:
            key: Key, index, slice, or path (string, int, or slice)
            
        Returns:
            Value at key/path/index/slice
            
        Raises:
            KeyError: If key/path doesn't exist
            IndexError: If index is out of range
            TypeError: If trying to index/slice non-list data
            
        Example:
            >>> data = XWData([{"name": "Alice"}, {"name": "Bob"}])
            >>> data[0]  # Returns {"name": "Alice"}
            >>> data[0:2]  # Returns [{"name": "Alice"}, {"name": "Bob"}]
            >>> data = XWData({"users": [{"name": "Alice"}, {"name": "Bob"}]})
            >>> data["users"]  # Returns list
            >>> data["users.0.name"]  # Returns "Alice"
            >>> data["users"][0]  # Returns {"name": "Alice"}
        """
        if not self._node:
            raise KeyError(f"Cannot access '{key}' - XWData is empty")
        
        # For integer indices and slices, delegate to XWDataNode which delegates to XWNode
        # This reuses XWNode's optimized indexing capabilities
        if isinstance(key, (int, slice)):
            # XWDataNode's __getitem__ now supports int and slice and delegates to XWNode
            return self._node[key]
        
        # For string keys, delegate to XWDataNode which delegates to XWNode
        # This reuses XWNode's optimized path navigation
        return self._node[key]
    
    def __setitem__(self, key: str, value: Any) -> None:
        """
        Set value using bracket notation with path support (COW semantics).
        
        Delegates to XWDataNode which delegates to XWNode for optimal COW performance.
        
        Args:
            key: Key or path (dot-separated)
            value: Value to set
            
        Example:
            >>> data = XWData({"users": []})
            >>> data["users.0"] = {"name": "Alice"}
            >>> data["count"] = 1
        """
        if not self._node:
            raise XWDataError("Cannot set value - XWData is empty")
        
        # Delegate to XWDataNode which handles COW via XWNode
        self._node[key] = value
        self._metadata = self._node.metadata
    
    def __delitem__(self, key: str) -> None:
        """
        Delete value using bracket notation with path support (COW semantics).
        
        Delegates to XWDataNode which delegates to XWNode for optimal COW performance.
        
        Args:
            key: Key or path (dot-separated)
            
        Raises:
            KeyError: If key/path doesn't exist
            
        Example:
            >>> data = XWData({"name": "test", "temp": "value"})
            >>> del data["temp"]
        """
        if not self._node:
            raise KeyError(f"Cannot delete '{key}' - XWData is empty")
        
        # Delegate to XWDataNode which handles COW via XWNode
        del self._node[key]
        self._metadata = self._node.metadata
    
    def __contains__(self, key: str) -> bool:
        """
        Check if key exists using 'in' operator.
        
        Delegates to XWDataNode which delegates to XWNode for optimal performance.
        
        Args:
            key: Key or path (dot-separated)
            
        Returns:
            True if key/path exists
            
        Example:
            >>> data = XWData({"users": [{"name": "Alice"}]})
            >>> "users" in data  # True
            >>> "users.0.name" in data  # True
            >>> "missing" in data  # False
        """
        if not self._node:
            return False
        
        # Delegate to XWDataNode which delegates to XWNode
        return key in self._node
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """
        Get value with default (like dict.get()).
        
        Delegates to XWDataNode which delegates to XWNode for optimal performance.
        
        Args:
            key: Key or path (dot-separated)
            default: Default value if key doesn't exist
            
        Returns:
            Value at key or default
            
        Example:
            >>> data = XWData({"name": "test"})
            >>> data.get_value("name")  # "test"
            >>> data.get_value("missing", "default")  # "default"
        """
        if not self._node:
            return default
        
        # Delegate to XWDataNode which delegates to XWNode
        return self._node.get_value_at_path(key, default=default)
    
    def __str__(self) -> str:
        """String representation."""
        return super().__str__()
    
    def __repr__(self) -> str:
        """Detailed representation."""
        return super().__repr__()
    
    # ==========================================================================
    # XWNODE INTEGRATION (Plan 1, Option A)
    # ==========================================================================
    
    def as_xwnode(self) -> 'XWNode':
        """
        Get the underlying XWNode for advanced operations.
        
        Enables integration with xwquery, xwschema, and other libraries
        that operate on XWNode instances.
        
        If XWNode doesn't exist (e.g., from hyper-fast path), it will be
        created on-demand from the node's data.
        
        Returns:
            XWNode: The internal immutable node with COW semantics
            
        Raises:
            ValueError: If no XWNode is available and data cannot be loaded
            
        Example:
            >>> data = await XWData.load('users.json')
            >>> node = data.as_xwnode()
            >>> from exonware.xwquery import XWQuery
            >>> result = XWQuery.execute("SELECT * FROM users WHERE age > 18", node)
        """
        from exonware.xwnode import XWNode
        
        if self._node and self._node._xwnode:
            return self._node._xwnode
        
        # If XWNode doesn't exist but we have data, create it on-demand
        # This handles cases where hyper-fast path skipped XWNode creation
        if self._node and self._node._data is not None:
            try:
                self._node._xwnode = XWNode.from_native(self._node._data, immutable=True)
                return self._node._xwnode
            except Exception as e:
                logger.debug(f"Failed to create XWNode on-demand: {e}")
        
        raise ValueError(
            "No XWNode available. Data may not be loaded yet or failed to initialize. "
            "For lazy file-backed data, access the data first (e.g., await data.get('')) "
            "to trigger lazy loading, or use the async query() method which handles this automatically. "
            "Try loading data with XWData.load() or creating with XWData.from_native()."
        )
    
    def as_xwdata(self) -> 'XWData':
        """
        Create a new XWData instance from this XWData.
        
        Useful for:
        - Creating a copy for chaining operations
        - Ensuring a fresh instance with the same data
        - Converting intermediate values to XWData for method chaining
        
        Returns:
            XWData: A new XWData instance with the same data
            
        Example:
            >>> data = XWData.from_native({"users": [{"name": "Alice"}]})
            >>> # Get a value and wrap it in XWData for chaining
            >>> users = data["users"].as_xwdata() if isinstance(data["users"], (dict, list)) else data["users"]
            >>> # Or simply create a copy
            >>> data_copy = data.as_xwdata()
        """
        # Create a new XWData instance from the native data
        native_data = self.to_native()
        return XWData.from_native(native_data, metadata=self._metadata.copy(), config=self._config)
    
    async def query(self, expression: str, format: str = 'sql', **opts) -> Any:
        """
        Execute a query on this data (convenience wrapper for XWQuery).
        
        This method provides single-call querying without needing to
        extract the XWNode first. For lazy file-backed data, this will
        automatically trigger lazy loading to create the XWNode.
        
        Args:
            expression: Query expression (SQL, JMESPath, GraphQL, etc.)
            format: Query format (default: 'sql')
            **opts: Additional query options
            
        Returns:
            Query results
            
        Example:
            >>> data = await XWData.load('users.json')
            >>> # SQL query (default)
            >>> result = await data.query("SELECT * FROM users WHERE age > 18")
            >>> # JMESPath query
            >>> result = await data.query("users[?age > `18`].name", format='jmespath')
            >>> # GraphQL query
            >>> result = await data.query("{ users(filter: {age: {gt: 18}}) { name } }", format='graphql')
        """
        try:
            from exonware.xwquery import XWQuery
        except ImportError:
            raise ImportError(
                "xwquery is required for query operations. "
                "Install with: pip install exonware-xwquery"
            )
        
        # For lazy file-backed data, trigger lazy load by accessing data
        # This ensures XWNode is created before querying
        if self._metadata.get('lazy_mode') == 'file' and (not self._node or not self._node._xwnode):
            # Trigger lazy load by getting root data (empty path gets entire data)
            try:
                _ = await self.get('')
            except Exception:
                # If get('') fails, try to_native() which should also trigger load
                _ = self.to_native()
        
        # Get XWNode (should be available now after lazy load if needed)
        node = self.as_xwnode()
        
        # Execute query
        result = XWQuery.execute(expression, node, format=format, **opts)
        
        return result
    
    # ==========================================================================
    # FORMAT MANAGEMENT
    # ==========================================================================
    
    def set_format(self, format_name: str) -> 'XWData':
        """
        Set the format for serialization/display operations.
        
        This overrides the detected format for all operations (print, save, serialize).
        The detected_format is preserved separately for reference.
        
        Args:
            format_name: Format name (e.g., 'JSON', 'XML', 'YAML', 'TOML', etc.)
                        Supports ALL registered serialization formats (50+)
        
        Returns:
            Self for method chaining
        
        Example:
            >>> data = XWData.from_native({'key': 'value'})
            >>> data.set_format('XML')
            >>> print(data)  # Prints as XML
            >>> 
            >>> data.set_format('YAML')
            >>> print(data)  # Prints as YAML
            >>> 
            >>> # Detected format is preserved
            >>> json_data = await XWData.load('config.json')
            >>> print(json_data.get_detected_format())  # 'JSON' (preserved)
            >>> json_data.set_format('XML')
            >>> print(json_data)  # Prints as XML (override)
            >>> print(json_data.get_detected_format())  # Still 'JSON' (original preserved)
        """
        # Set user format override in metadata
        self._metadata['set_format'] = format_name.upper()
        
        # Also update node metadata if available
        if self._node:
            self._node.set_metadata('set_format', format_name.upper())
        
        return self  # Return self for chaining
    
    def get_active_format(self) -> str:
        """
        Get the active format being used for operations.
        
        Returns the format in this priority:
        1. set_format (user override)
        2. detected_format (from file)
        3. 'JSON' (default)
        
        Returns:
            Active format name
        
        Example:
            >>> data = await XWData.load('config.json')
            >>> print(data.get_active_format())  # 'JSON'
            >>> data.set_format('YAML')
            >>> print(data.get_active_format())  # 'YAML'
        """
        return (
            self._metadata.get('set_format') or 
            self._metadata.get('detected_format') or 
            'JSON'
        )
    
    def clear_format_override(self) -> 'XWData':
        """
        Clear the format override, reverting to detected format.
        
        Returns:
            Self for method chaining
        
        Example:
            >>> data = await XWData.load('config.json')  # Detected as JSON
            >>> data.set_format('XML')
            >>> print(data)  # Prints as XML
            >>> data.clear_format_override()
            >>> print(data)  # Prints as JSON again (detected format)
        """
        if 'set_format' in self._metadata:
            del self._metadata['set_format']
        
        if self._node:
            # Remove from node metadata too
            node_meta = self._node.metadata
            if 'set_format' in node_meta:
                self._node.set_metadata('set_format', None)
        
        return self
    
    # ==========================================================================
    # DETECTION METADATA (Plan 3, Option A)
    # ==========================================================================
    
    def get_detected_format(self) -> Optional[str]:
        """
        Get the auto-detected format for this data.
        
        Returns:
            Format name (e.g., 'JSON', 'YAML') or None if not detected
            
        Example:
            >>> data = await XWData.load('config.json')
            >>> print(data.get_detected_format())
            'JSON'
        """
        return self._metadata.get('detected_format')
    
    def get_detection_confidence(self) -> Optional[float]:
        """
        Get the confidence score for format detection.
        
        Returns:
            Confidence score (0.0-1.0) or None
            
        Example:
            >>> data = await XWData.load('config.yml')
            >>> print(f"Detected as {data.get_detected_format()} with {data.get_detection_confidence():.0%} confidence")
            'Detected as YAML with 95% confidence'
        """
        return self._metadata.get('detection_confidence')
    
    def get_detection_info(self) -> dict[str, Any]:
        """
        Get complete detection information.
        
        Returns:
            Dictionary with detection metadata:
            - detected_format: Format name
            - detection_confidence: Confidence score (0.0-1.0)
            - detection_method: 'extension' | 'content' | 'hint'
            - format_candidates: dict of format -> confidence
            
        Example:
            >>> data = await XWData.load('data.json')
            >>> info = data.get_detection_info()
            >>> print(info)
            {
                'detected_format': 'JSON',
                'detection_confidence': 0.95,
                'detection_method': 'extension',
                'format_candidates': {'JSON': 0.95, 'YAML': 0.2}
            }
        """
        detected = self._metadata.get('detected_format')
        method = self._metadata.get('detection_method')
        
        # For explicit hints, preserve user-provided style (typically lower-case),
        # while internal engine/serializer logic can still use upper-case.
        if detected and method == 'hint':
            detected_display = detected.lower()
        else:
            detected_display = detected
        
        return {
            'detected_format': detected_display,
            'detection_confidence': self._metadata.get('detection_confidence'),
            'detection_method': method,
            'format_candidates': self._metadata.get('format_candidates', {})
        }


# ==============================================================================
# CONVENIENCE FUNCTIONS
# ==============================================================================

async def load(path: Union[str, Path], **opts) -> XWData:
    """
    Convenience function to load data (async).
    
    Args:
        path: File path
        **opts: Options
        
    Returns:
        XWData instance
    """
    return await XWData.load(path, **opts)


def from_native(data: Union[dict, list], **opts) -> XWData:
    """
    Convenience function to create from native data (sync).
    
    Args:
        data: Native data
        **opts: Options
        
    Returns:
        XWData instance
    """
    return XWData.from_native(data, **opts)


async def parse(content: Union[str, bytes], format: Union[str, DataFormat], **opts) -> XWData:
    """
    Convenience function to parse content (async).
    
    Args:
        content: Content to parse
        format: Format name
        **opts: Options
        
    Returns:
        XWData instance
    """
    return await XWData.parse(content, format, **opts)


# ==============================================================================
# EXPORTS
# ==============================================================================

__all__ = [
    'XWData',
    'load',
    'from_native',
    'parse',
]

