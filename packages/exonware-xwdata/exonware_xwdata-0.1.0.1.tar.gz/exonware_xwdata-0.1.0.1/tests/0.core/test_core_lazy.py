#!/usr/bin/env python3
"""
#exonware/xwdata/tests/0.core/test_core_lazy.py

Core tests for lazy loading - 80/20 rule.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1
Generation Date: 28-Oct-2025
"""

import pytest
from pathlib import Path

from exonware.xwdata.data.lazy import LazyFileProxy, LazySerializationProxy, LazyXWNodeProxy


@pytest.mark.xwdata_core
class TestCoreLazyLoading:
    """Core lazy loading tests - fast, high-value."""
    
    @pytest.mark.asyncio
    async def test_lazy_file_proxy_defers_loading(self, tmp_path):
        """Test LazyFileProxy defers file loading."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        # Create lazy proxy
        async def loader(path):
            return path.read_text()
        
        proxy = LazyFileProxy(test_file, loader)
        
        # Should not be loaded yet
        assert not proxy.is_loaded
        
        # Load on first access
        data = await proxy.get_data()
        assert data == "Test content"
        assert proxy.is_loaded
    
    @pytest.mark.asyncio
    async def test_lazy_serialization_proxy_defers_parsing(self):
        """Test LazySerializationProxy defers parsing."""
        import json
        
        # Create lazy proxy with JSON content
        content = '{"key": "value", "number": 42}'
        
        async def parser(content, format_hint):
            return json.loads(content)
        
        proxy = LazySerializationProxy(content, parser, "JSON")
        
        # Should not be parsed yet
        assert not proxy.is_parsed
        assert proxy.content_size > 0
        
        # Parse on first access
        data = await proxy.get_data()
        assert data == {"key": "value", "number": 42}
        assert proxy.is_parsed
    
    @pytest.mark.asyncio
    async def test_lazy_xwnode_proxy_defers_creation(self):
        """Test LazyXWNodeProxy defers node creation."""
        test_data = {"key": "value"}
        
        async def factory(data):
            # Simulate node creation
            return f"Node({data})"
        
        proxy = LazyXWNodeProxy(test_data, factory)
        
        # Should not be created yet
        assert not proxy.is_created
        
        # Can access raw data without creating node
        direct_data = proxy.get_data_direct()
        assert direct_data == test_data
        assert not proxy.is_created
        
        # Create node on first navigation
        node = await proxy.get_node()
        assert node == "Node({'key': 'value'})"
        assert proxy.is_created
    
    @pytest.mark.asyncio
    async def test_lazy_proxy_caches_result(self, tmp_path):
        """Test lazy proxies cache loaded results."""
        test_file = tmp_path / "cache_test.txt"
        test_file.write_text("Cached content")
        
        load_count = 0
        
        async def counting_loader(path):
            nonlocal load_count
            load_count += 1
            return path.read_text()
        
        proxy = LazyFileProxy(test_file, counting_loader)
        
        # Load multiple times
        data1 = await proxy.get_data()
        data2 = await proxy.get_data()
        data3 = await proxy.get_data()
        
        # Should only load once
        assert load_count == 1
        assert data1 == data2 == data3 == "Cached content"
    
    @pytest.mark.asyncio
    async def test_lazy_proxy_handles_errors(self, tmp_path):
        """Test lazy proxy error handling."""
        async def failing_loader(path):
            raise ValueError("Load failed")
        
        proxy = LazyFileProxy(tmp_path / "nonexistent.txt", failing_loader)
        
        # Should raise error on access
        with pytest.raises(ValueError, match="Load failed"):
            await proxy.get_data()
        
        # Should be marked as loaded (even with error)
        assert proxy.is_loaded


@pytest.mark.xwdata_core
@pytest.mark.xwdata_performance
class TestCoreLazyPerformance:
    """Performance tests for lazy loading."""
    
    @pytest.mark.asyncio
    async def test_lazy_saves_memory(self, tmp_path):
        """Test lazy loading reduces memory usage."""
        import sys
        
        # Create large content
        large_content = "x" * (1024 * 1024)  # 1MB
        test_file = tmp_path / "large.txt"
        test_file.write_text(large_content)
        
        async def loader(path):
            return path.read_text()
        
        # Lazy proxy (unloaded)
        proxy = LazyFileProxy(test_file, loader)
        proxy_size = sys.getsizeof(proxy)
        
        # Direct load
        direct_data = test_file.read_text()
        direct_size = sys.getsizeof(direct_data)
        
        # Lazy should be much smaller when unloaded
        assert proxy_size < direct_size / 10

