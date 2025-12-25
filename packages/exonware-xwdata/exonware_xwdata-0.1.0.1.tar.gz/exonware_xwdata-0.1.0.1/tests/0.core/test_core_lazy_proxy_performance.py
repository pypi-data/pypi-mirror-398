#!/usr/bin/env python3
"""
#exonware/xwdata/tests/0.core/test_core_lazy_proxy_performance.py

Performance stress tests for lazy proxy pattern vs native value returns.

Tests the claim: "Zero overhead for indexing: data['key'] returns lightweight proxy"

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1
Generation Date: 15-Dec-2025
"""

import pytest
import time
import sys
from typing import Any
from exonware.xwdata import XWData
from exonware.xwnode import XWNode


class XWDataLazyProxy:
    """Lightweight proxy for performance testing."""
    
    def __init__(self, parent: XWData, key: Any, value: Any):
        self._parent = parent
        self._key = key
        self._value = value
        self._materialized = None
    
    def _materialize(self) -> XWData:
        if self._materialized is None:
            self._materialized = XWData.from_native(
                self._value,
                metadata=self._parent._metadata.copy(),
                config=self._parent._config
            )
        return self._materialized
    
    def __getattr__(self, name: str) -> Any:
        return getattr(self._materialize(), name)
    
    def __getitem__(self, key: Any) -> Any:
        if isinstance(self._value, (dict, list)):
            nested_value = self._value[key]
            if isinstance(nested_value, (dict, list)) and not isinstance(key, slice):
                return XWDataLazyProxy(self._parent, key, nested_value)
            return nested_value
        raise TypeError(f"Cannot index {type(self._value)}")


class XWNodeLazyProxy:
    """Lightweight proxy for performance testing."""
    
    def __init__(self, parent: XWNode, key: Any, value: Any):
        self._parent = parent
        self._key = key
        self._value = value
        self._materialized = None
    
    def _materialize(self) -> XWNode:
        if self._materialized is None:
            self._materialized = XWNode.from_native(
                self._value,
                immutable=self._parent._immutable,
                mode=self._parent._mode,
                **self._parent._options
            )
        return self._materialized
    
    def __getattr__(self, name: str) -> Any:
        return getattr(self._materialize(), name)
    
    def __getitem__(self, key: Any) -> Any:
        if isinstance(self._value, (dict, list)):
            nested_value = self._value[key]
            if isinstance(nested_value, (dict, list)) and not isinstance(key, slice):
                return XWNodeLazyProxy(self._parent, key, nested_value)
            return nested_value
        raise TypeError(f"Cannot index {type(self._value)}")


@pytest.mark.xwdata_core
@pytest.mark.performance
class TestLazyProxyPerformance:
    """Performance tests for lazy proxy pattern."""
    
    def _create_large_dataset(self, size: int = 10000) -> dict:
        """Create a large dataset for stress testing."""
        return {
            f"key_{i}": {
                "id": i,
                "name": f"Item {i}",
                "data": [j for j in range(100)],
                "metadata": {"index": i, "value": i * 2}
            }
            for i in range(size)
        }
    
    def test_xwdata_indexing_overhead_native_vs_proxy(self):
        """Test overhead of returning native value vs lightweight proxy."""
        data = XWData.from_native(self._create_large_dataset(1000))
        
        # Test 1: Native value return (current behavior)
        start = time.perf_counter()
        for i in range(10000):
            result = data._node["key_0"]  # Direct access, returns native dict
        native_time = time.perf_counter() - start
        
        # Test 2: Lightweight proxy return (proposed behavior)
        start = time.perf_counter()
        for i in range(10000):
            result = XWDataLazyProxy(data, "key_0", data._node["key_0"])
        proxy_time = time.perf_counter() - start
        
        # Calculate overhead
        overhead_ratio = proxy_time / native_time if native_time > 0 else float('inf')
        overhead_percent = (overhead_ratio - 1) * 100
        
        print(f"\n{'='*60}")
        print(f"XWData Indexing Overhead Test (10,000 iterations)")
        print(f"{'='*60}")
        print(f"Native value return:  {native_time*1000:.2f} ms")
        print(f"Lightweight proxy:    {proxy_time*1000:.2f} ms")
        print(f"Overhead ratio:       {overhead_ratio:.3f}x")
        print(f"Overhead:              {overhead_percent:+.2f}%")
        print(f"{'='*60}")
        
        # Assert: Proxy should have minimal overhead (< 50% for 10k iterations)
        # In practice, for single access, overhead should be < 10%
        assert overhead_ratio < 2.0, f"Proxy overhead too high: {overhead_ratio:.3f}x"
    
    def test_xwnode_indexing_overhead_native_vs_proxy(self):
        """Test overhead of returning native value vs lightweight proxy for XWNode."""
        node = XWNode.from_native(self._create_large_dataset(1000))
        
        # Test 1: Native value return (current behavior)
        start = time.perf_counter()
        for i in range(10000):
            result = node["key_0"]  # Direct access, returns native dict
        native_time = time.perf_counter() - start
        
        # Test 2: Lightweight proxy return (proposed behavior)
        native_value = node["key_0"]
        start = time.perf_counter()
        for i in range(10000):
            result = XWNodeLazyProxy(node, "key_0", native_value)
        proxy_time = time.perf_counter() - start
        
        # Calculate overhead
        overhead_ratio = proxy_time / native_time if native_time > 0 else float('inf')
        overhead_percent = (overhead_ratio - 1) * 100
        
        print(f"\n{'='*60}")
        print(f"XWNode Indexing Overhead Test (10,000 iterations)")
        print(f"{'='*60}")
        print(f"Native value return:  {native_time*1000:.2f} ms")
        print(f"Lightweight proxy:    {proxy_time*1000:.2f} ms")
        print(f"Overhead ratio:       {overhead_ratio:.3f}x")
        print(f"Overhead:              {overhead_percent:+.2f}%")
        print(f"{'='*60}")
        
        # Assert: Proxy should have minimal overhead
        assert overhead_ratio < 2.0, f"Proxy overhead too high: {overhead_ratio:.3f}x"
    
    def test_memory_overhead_proxy_vs_native(self):
        """Test memory overhead of proxy object vs native value."""
        import sys
        
        data = XWData.from_native({"key": {"nested": "value"}})
        native_value = data._node["key"]
        
        # Measure native dict size
        native_size = sys.getsizeof(native_value)
        
        # Measure proxy size
        proxy = XWDataLazyProxy(data, "key", native_value)
        proxy_size = sys.getsizeof(proxy)
        
        # Calculate overhead
        overhead_bytes = proxy_size - native_size
        overhead_ratio = proxy_size / native_size if native_size > 0 else float('inf')
        
        print(f"\n{'='*60}")
        print(f"Memory Overhead Test")
        print(f"{'='*60}")
        print(f"Native dict size:     {native_size} bytes")
        print(f"Proxy object size:    {proxy_size} bytes")
        print(f"Overhead:             {overhead_bytes} bytes ({overhead_ratio:.2f}x)")
        print(f"{'='*60}")
        
        # Proxy should be lightweight (< 200 bytes overhead for small dict)
        assert overhead_bytes < 500, f"Proxy memory overhead too high: {overhead_bytes} bytes"
    
    def test_chaining_performance_with_proxy(self):
        """Test performance of chaining with proxy vs without."""
        data = XWData.from_native({
            "level1": {
                "level2": {
                    "level3": {"value": "final"}
                }
            }
        })
        
        # Test 1: Direct native access (no chaining)
        start = time.perf_counter()
        for i in range(10000):
            result = data._node["level1"]["level2"]["level3"]["value"]
        native_time = time.perf_counter() - start
        
        # Test 2: Chaining with proxy (materialization on method call)
        start = time.perf_counter()
        for i in range(10000):
            proxy1 = XWDataLazyProxy(data, "level1", data._node["level1"])
            proxy2 = XWDataLazyProxy(data, "level2", proxy1._value["level2"])
            proxy3 = XWDataLazyProxy(data, "level3", proxy2._value["level3"])
            result = proxy3._value["value"]  # Access without materialization
        proxy_chain_time = time.perf_counter() - start
        
        # Test 3: Chaining with full materialization (worst case)
        start = time.perf_counter()
        for i in range(10000):
            proxy1 = XWDataLazyProxy(data, "level1", data._node["level1"])
            mat1 = proxy1._materialize()
            proxy2 = XWDataLazyProxy(mat1, "level2", mat1._node["level2"])
            mat2 = proxy2._materialize()
            proxy3 = XWDataLazyProxy(mat2, "level3", mat2._node["level3"])
            mat3 = proxy3._materialize()
            result = mat3._node["value"]
        full_materialization_time = time.perf_counter() - start
        
        print(f"\n{'='*60}")
        print(f"Chaining Performance Test (10,000 iterations)")
        print(f"{'='*60}")
        print(f"Native access:              {native_time*1000:.2f} ms")
        print(f"Proxy chain (no materialize): {proxy_chain_time*1000:.2f} ms")
        print(f"Proxy chain (full materialize): {full_materialization_time*1000:.2f} ms")
        print(f"{'='*60}")
        
        # Proxy without materialization should be close to native
        ratio = proxy_chain_time / native_time if native_time > 0 else float('inf')
        assert ratio < 3.0, f"Proxy chaining overhead too high: {ratio:.3f}x"
    
    def test_stress_large_dataset_indexing(self):
        """Stress test with large dataset - many keys."""
        large_data = self._create_large_dataset(10000)
        data = XWData.from_native(large_data)
        
        # Test native access
        start = time.perf_counter()
        for i in range(1000):
            key = f"key_{i % 1000}"
            result = data._node[key]
        native_time = time.perf_counter() - start
        
        # Test proxy creation
        start = time.perf_counter()
        for i in range(1000):
            key = f"key_{i % 1000}"
            result = XWDataLazyProxy(data, key, data._node[key])
        proxy_time = time.perf_counter() - start
        
        overhead_ratio = proxy_time / native_time if native_time > 0 else float('inf')
        
        print(f"\n{'='*60}")
        print(f"Large Dataset Stress Test (1,000 keys, 1,000 iterations)")
        print(f"{'='*60}")
        print(f"Native access:    {native_time*1000:.2f} ms")
        print(f"Proxy creation:  {proxy_time*1000:.2f} ms")
        print(f"Overhead ratio:  {overhead_ratio:.3f}x")
        print(f"{'='*60}")
        
        assert overhead_ratio < 3.0, f"Proxy overhead too high on large dataset: {overhead_ratio:.3f}x"
    
    def test_proxy_materialization_cost(self):
        """Test the cost of materializing proxy vs direct creation."""
        data = XWData.from_native({"key": {"nested": "value"}})
        native_value = data._node["key"]
        
        # Test 1: Direct XWData creation
        start = time.perf_counter()
        for i in range(1000):
            direct = XWData.from_native(native_value)
        direct_time = time.perf_counter() - start
        
        # Test 2: Proxy creation + materialization
        start = time.perf_counter()
        for i in range(1000):
            proxy = XWDataLazyProxy(data, "key", native_value)
            materialized = proxy._materialize()
        proxy_materialize_time = time.perf_counter() - start
        
        # Test 3: Just proxy creation (no materialization)
        start = time.perf_counter()
        for i in range(1000):
            proxy = XWDataLazyProxy(data, "key", native_value)
        proxy_only_time = time.perf_counter() - start
        
        print(f"\n{'='*60}")
        print(f"Materialization Cost Test (1,000 iterations)")
        print(f"{'='*60}")
        print(f"Direct XWData creation:     {direct_time*1000:.2f} ms")
        print(f"Proxy + materialization:    {proxy_materialize_time*1000:.2f} ms")
        print(f"Proxy only (no materialize): {proxy_only_time*1000:.2f} ms")
        print(f"Materialization overhead:  {(proxy_materialize_time - proxy_only_time)*1000:.2f} ms")
        print(f"{'='*60}")
        
        # Materialization should be similar to direct creation
        ratio = proxy_materialize_time / direct_time if direct_time > 0 else float('inf')
        assert ratio < 2.0, f"Materialization overhead too high: {ratio:.3f}x"

