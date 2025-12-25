#!/usr/bin/env python3
"""
#exonware/xwdata/tests/1.unit/operations_tests/test_integration.py

Integration tests for xwdata operations with xwsystem.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.3
Generation Date: October 27, 2025

Tests following 5 priorities:
1. Security - Safe integration
2. Usability - Simple API
3. Maintainability - Clean integration
4. Performance - Efficient operations
5. Extensibility - xwsystem patterns work
"""

import pytest
from exonware.xwdata import (
    XWDataBuilder,
    merge_data, diff_data, patch_data,
    quick_load, quick_merge, quick_diff,
    batch_convert,
    MergeStrategy, DiffMode
)


@pytest.mark.xwdata_unit
class TestXWDataBuilderPattern:
    """Test builder pattern integration (Priority #2: Usability)."""
    
    def test_builder_basic_construction(self):
        """Test basic builder construction."""
        builder = XWDataBuilder()
        data = (builder
                .set("name", "Alice")
                .set("age", 30)
                .build())
        
        assert data is not None
        # Verify data was built correctly
        native = data.to_native()
        assert native["name"] == "Alice"
        assert native["age"] == 30
    
    def test_builder_nested_paths(self):
        """Test builder with nested paths."""
        data = (XWDataBuilder()
                .set("user.name", "Bob")
                .set("user.email", "bob@example.com")
                .set("user.settings.theme", "dark")
                .build())
        
        native = data.to_native()
        assert native["user"]["name"] == "Bob"
        assert native["user"]["settings"]["theme"] == "dark"
    
    def test_builder_with_lists(self):
        """Test builder with list append."""
        data = (XWDataBuilder()
                .set("name", "Charlie")
                .append("skills", "Python")
                .append("skills", "JavaScript")
                .build())
        
        native = data.to_native()
        assert native["name"] == "Charlie"
        assert "Python" in native["skills"]
        assert "JavaScript" in native["skills"]


@pytest.mark.xwdata_unit
@pytest.mark.xwdata_integration
class TestXWSystemIntegration:
    """Test xwsystem.operations integration."""
    
    def test_merge_data_integration(self):
        """Test merge_data uses xwsystem.operations."""
        target = {"a": 1, "b": {"c": 2}}
        source = {"b": {"d": 3}}
        
        result = merge_data(target, source, strategy=MergeStrategy.DEEP)
        
        # Should use xwsystem's deep_merge
        assert result is not None
    
    def test_diff_data_integration(self):
        """Test diff_data uses xwsystem.operations."""
        original = {"a": 1, "b": 2}
        modified = {"a": 1, "b": 3}
        
        result = diff_data(original, modified, mode=DiffMode.FULL)
        
        # Should return DiffResult from xwsystem
        assert hasattr(result, 'total_changes')
        assert hasattr(result, 'operations')
        assert result.total_changes > 0
    
    def test_patch_data_integration(self):
        """Test patch_data uses xwsystem.operations."""
        data = {"a": 1}
        operations = [{"op": "add", "path": "/b", "value": 2}]
        
        result = patch_data(data, operations)
        
        # Should return PatchResult from xwsystem
        assert hasattr(result, 'success')
        assert result.success


@pytest.mark.xwdata_unit  
@pytest.mark.xwdata_usability
class TestShortcutsAPI:
    """Test shortcuts API (Priority #2: Usability)."""
    
    def test_quick_merge_shortcut(self):
        """Test quick_merge convenience function."""
        result = quick_merge(
            {"a": 1},
            {"b": 2}
        )
        
        # Should return merged data
        assert result is not None
    
    def test_quick_diff_shortcut(self):
        """Test quick_diff convenience function."""
        result = quick_diff(
            {"a": 1},
            {"a": 2}
        )
        
        # Should return dict with diff info
        assert "total_changes" in result
        assert result["total_changes"] > 0


@pytest.mark.xwdata_unit
@pytest.mark.xwdata_performance
class TestBatchOperations:
    """Test batch operations (Priority #4: Performance)."""
    
    def test_batch_convert_basic(self):
        """Test basic batch conversion."""
        items = [
            {"id": 1, "name": "Item 1"},
            {"id": 2, "name": "Item 2"},
            {"id": 3, "name": "Item 3"}
        ]
        
        results = batch_convert(items, "json")
        
        # Should convert all items
        assert len(results) == 3
        assert all(r is not None for r in results)

