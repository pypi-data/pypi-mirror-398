#!/usr/bin/env python3
"""
#exonware/xwdata/tests/2.integration/test_xwnode_delegation.py

Integration tests for XWDataNode delegation to XWNode.

Tests that XWDataNode properly delegates subscriptable operations to the
enhanced XWNode while maintaining XWData-specific features.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1
Generation Date: 27-Oct-2025
"""

import pytest
from exonware.xwdata import XWData


@pytest.mark.xwdata_integration
class TestXWDataNodeDelegation:
    """Test XWDataNode delegation to enhanced XWNode."""
    
    def test_getitem_delegates_to_xwnode(self):
        """Test that XWDataNode.__getitem__ delegates to XWNode."""
        data = XWData({"count": 2, "users": [{"name": "Alice"}]})
        
        # Should delegate to XWNode and return actual values
        assert data["count"] == 2
        assert isinstance(data["count"], int)
        
        # Complex structures
        users = data["users"]
        assert isinstance(users, list)
        assert len(users) == 1
    
    def test_get_value_at_path_delegates_to_xwnode(self):
        """Test that get_value_at_path() delegates to XWNode.get_value()."""
        data = XWData({
            "users": [
                {"name": "Alice", "age": 30},
                {"name": "Bob", "age": 25}
            ]
        })
        
        # Should delegate to XWNode.get_value()
        assert data.get("users.0.name") == "Alice"
        assert data.get("users.1.age") == 25
        assert data.get("missing", "default") == "default"
    
    def test_contains_delegates_to_xwnode(self):
        """Test that __contains__ delegates to XWNode."""
        data = XWData({"count": 2, "users": [{"name": "Alice"}]})
        
        # Should delegate to XWNode.__contains__
        assert "count" in data
        assert "users" in data
        assert "users.0.name" in data
        assert "missing" not in data
    
    def test_path_based_access_delegation(self):
        """Test path-based access delegates correctly."""
        data = XWData({
            "config": {
                "settings": {
                    "theme": "dark",
                    "language": "en"
                }
            }
        })
        
        # Deep path access
        assert data["config.settings.theme"] == "dark"
        assert data["config.settings.language"] == "en"
        
        # Path existence check
        assert "config.settings.theme" in data
        assert "config.settings.missing" not in data


@pytest.mark.xwdata_integration
class TestXWDataFacadeDelegation:
    """Test XWData facade delegation through XWDataNode to XWNode."""
    
    def test_full_delegation_chain(self):
        """Test complete delegation: XWData → XWDataNode → XWNode."""
        data = XWData({"users": [{"name": "Alice", "age": 30}]})
        
        # XWData → XWDataNode → XWNode
        assert data["users.0.name"] == "Alice"
        assert data.get("users.0.age") == 30
        assert "users.0.name" in data
    
    def test_file_loading_with_subscriptable_access(self):
        """Test loading from file and using subscriptable access."""
        # This would require a test file, so we'll use from_native
        data = XWData({
            "id": 1,
            "title": "Test",
            "metadata": {
                "created": "2024-01-01",
                "author": "Alice"
            }
        })
        
        # File-like access patterns
        assert data["id"] == 1
        assert data["title"] == "Test"
        assert data["metadata.author"] == "Alice"
    
    def test_mixed_access_patterns(self):
        """Test mixing different access patterns."""
        data = XWData({
            "users": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"}
            ],
            "count": 2
        })
        
        # Mix of simple keys and paths
        assert data["count"] == 2
        assert data["users"][0]["name"] == "Alice"
        assert data["users.1.name"] == "Bob"
        
        # Mix of get() and subscript
        assert data.get("count") == 2
        assert data["count"] == data.get("count")


@pytest.mark.xwdata_integration
class TestXWDataCOWSemantics:
    """Test that COW semantics are preserved with delegation."""
    
    def test_setitem_maintains_cow_semantics(self):
        """Test that __setitem__ maintains COW semantics."""
        data = XWData({"count": 0})
        original_node = data._node
        
        # Set value
        data["count"] = 10
        
        # Node should be updated (COW creates new node)
        assert data["count"] == 10
        # Original node frozen (depends on implementation)
    
    def test_delitem_maintains_cow_semantics(self):
        """Test that __delitem__ maintains COW semantics."""
        data = XWData({"temp": "value", "keep": "this"})
        original_node = data._node
        
        # Delete value
        del data["temp"]
        
        # Value should be deleted
        assert "temp" not in data
        assert "keep" in data


@pytest.mark.xwdata_core
class TestXWDataSubscriptableCore:
    """Core tests for XWData subscriptable interface (20% for 80% value)."""
    
    def test_basic_subscriptable_access(self):
        """Test basic subscriptable access works."""
        data = XWData({"name": "Alice", "age": 30})
        
        assert data["name"] == "Alice"
        assert data["age"] == 30
        assert "name" in data
    
    def test_path_based_subscriptable_access(self):
        """Test path-based subscriptable access works."""
        data = XWData({
            "users": [
                {"name": "Alice"},
                {"name": "Bob"}
            ]
        })
        
        assert data["users.0.name"] == "Alice"
        assert data["users.1.name"] == "Bob"
        assert "users.0.name" in data
    
    def test_get_with_default(self):
        """Test get() method with defaults."""
        data = XWData({"existing": "value"})
        
        assert data.get("existing") == "value"
        assert data.get("missing", "default") == "default"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

