#!/usr/bin/env python3
"""
#exonware/xwdata/src/exonware/xwdata/data/lazy.py

Lazy Loading Proxies

Implements Virtual Proxy pattern for deferred file I/O and serialization.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 28-Oct-2025
"""

from typing import Any, Optional, Callable
from pathlib import Path
from exonware.xwsystem import get_logger

logger = get_logger(__name__)


class LazyFileProxy:
    """
    Lazy file proxy - defers file reading until first access.
    
    Implements Virtual Proxy pattern following GUIDELINES_DEV.md:
    - Lazy Initialization: Load file only when accessed
    - Memory Efficiency: Reduce memory footprint
    - Performance: Avoid unnecessary I/O
    
    Priority #4: Performance - Deferred loading saves time and memory
    """
    
    def __init__(self, file_path: Path, loader_func: Callable):
        """
        Initialize lazy file proxy.
        
        Args:
            file_path: Path to file
            loader_func: Function to call for loading (async)
        """
        self._file_path = file_path
        self._loader_func = loader_func
        self._loaded = False
        self._data = None
        self._error = None
    
    async def _ensure_loaded(self):
        """Ensure data is loaded."""
        if not self._loaded:
            try:
                logger.debug(f"Lazy loading file: {self._file_path}")
                self._data = await self._loader_func(self._file_path)
                self._loaded = True
            except Exception as e:
                self._error = e
                self._loaded = True
                raise
    
    async def get_data(self) -> Any:
        """
        Get data, loading if necessary.
        
        Returns:
            Loaded data
        """
        await self._ensure_loaded()
        if self._error:
            raise self._error
        return self._data
    
    @property
    def is_loaded(self) -> bool:
        """Check if data is loaded."""
        return self._loaded
    
    def __repr__(self) -> str:
        status = "loaded" if self._loaded else "unloaded"
        return f"LazyFileProxy({self._file_path}, {status})"


class LazySerializationProxy:
    """
    Lazy serialization proxy - defers parsing until first access.
    
    Implements Virtual Proxy pattern:
    - Lazy Parsing: Parse content only when accessed
    - Memory Efficiency: Keep raw bytes until needed
    - Performance: Avoid unnecessary parsing
    
    Priority #4: Performance - Deferred parsing for unused data
    """
    
    def __init__(self, content: str, parser_func: Callable, format_hint: Optional[str] = None):
        """
        Initialize lazy serialization proxy.
        
        Args:
            content: Raw content
            parser_func: Function to parse content
            format_hint: Optional format hint
        """
        self._content = content
        self._parser_func = parser_func
        self._format_hint = format_hint
        self._parsed = False
        self._data = None
        self._error = None
    
    async def _ensure_parsed(self):
        """Ensure content is parsed."""
        if not self._parsed:
            try:
                logger.debug(f"Lazy parsing content ({len(self._content)} bytes)")
                self._data = await self._parser_func(self._content, self._format_hint)
                self._parsed = True
                # Clear content to save memory after parsing
                self._content = None
            except Exception as e:
                self._error = e
                self._parsed = True
                raise
    
    async def get_data(self) -> Any:
        """
        Get parsed data, parsing if necessary.
        
        Returns:
            Parsed data
        """
        await self._ensure_parsed()
        if self._error:
            raise self._error
        return self._data
    
    @property
    def is_parsed(self) -> bool:
        """Check if content is parsed."""
        return self._parsed
    
    @property
    def content_size(self) -> int:
        """Get content size in bytes."""
        if self._content:
            return len(self._content)
        return 0
    
    def __repr__(self) -> str:
        status = "parsed" if self._parsed else "unparsed"
        size = self.content_size
        return f"LazySerializationProxy({status}, {size} bytes)"


class LazyXWNodeProxy:
    """
    Lazy XWNode proxy - defers node creation until first navigation.
    
    Implements Virtual Proxy pattern:
    - Lazy Node Creation: Create XWNode only when navigating
    - Memory Efficiency: Keep plain dict until needed
    - Performance: Faster for simple dict access
    
    Priority #4: Performance - Avoid XWNode overhead for simple access
    """
    
    def __init__(self, data: Any, node_factory: Callable):
        """
        Initialize lazy XWNode proxy.
        
        Args:
            data: Native data
            node_factory: Function to create node
        """
        self._data = data
        self._node_factory = node_factory
        self._node = None
        self._created = False
    
    async def _ensure_node(self):
        """Ensure node is created."""
        if not self._created:
            logger.debug(f"Lazy creating XWNode for data")
            self._node = await self._node_factory(self._data)
            self._created = True
    
    async def get_node(self):
        """
        Get node, creating if necessary.
        
        Returns:
            XWNode instance
        """
        await self._ensure_node()
        return self._node
    
    def get_data_direct(self) -> Any:
        """
        Get raw data without creating node.
        
        Returns:
            Raw data (dict, list, etc.)
        """
        return self._data
    
    @property
    def is_created(self) -> bool:
        """Check if node is created."""
        return self._created
    
    def __repr__(self) -> str:
        status = "created" if self._created else "not created"
        return f"LazyXWNodeProxy({status})"


__all__ = ['LazyFileProxy', 'LazySerializationProxy', 'LazyXWNodeProxy']

