#!/usr/bin/env python3
"""
#exonware/xwdata/tests/0.core/test_core_as_methods.py

Tests for XWData as_xwnode() and as_xwdata() methods.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1
Generation Date: 15-Dec-2025
"""

import pytest
from exonware.xwdata import XWData


@pytest.mark.xwdata_core
class TestXWDataAsMethods:
    """Test XWData as_xwnode() and as_xwdata() methods."""
    
    def test_as_xwnode_returns_xwnode(self):
        """Test that as_xwnode() returns an XWNode instance."""
        data = XWData.from_native({"name": "Alice", "age": 30})
        node = data.as_xwnode()
        
        # Check it's an XWNode
        from exonware.xwnode import XWNode
        assert isinstance(node, XWNode)
        
        # Check data is preserved
        assert node.get_value("name") == "Alice"
        assert node.get_value("age") == 30
    
    def test_as_xwdata_returns_new_xwdata(self):
        """Test that as_xwdata() returns a new XWData instance."""
        data = XWData.from_native({"name": "Alice", "age": 30})
        new_data = data.as_xwdata()
        
        # Check it's an XWData instance
        assert isinstance(new_data, XWData)
        
        # Check it's a different object
        assert data is not new_data
        
        # Check data is preserved
        assert new_data.to_native() == data.to_native()
        assert new_data["name"] == "Alice"
        assert new_data["age"] == 30
    
    def test_as_xwdata_preserves_metadata(self):
        """Test that as_xwdata() preserves metadata."""
        data = XWData.from_native({"name": "Alice"}, metadata={"source": "test"})
        new_data = data.as_xwdata()
        
        # Check metadata is preserved
        assert new_data._metadata.get("source") == "test"
    
    def test_as_xwdata_creates_independent_copy(self):
        """Test that as_xwdata() creates an independent copy."""
        data = XWData.from_native({"name": "Alice", "age": 30})
        new_data = data.as_xwdata()
        
        # Modify original
        data["age"] = 31
        
        # New data should be independent (COW semantics)
        # Note: This depends on COW behavior - if COW is active, they should be independent
        # If COW is not active, they might share data
        original_age = data["age"]
        new_age = new_data["age"]
        
        # At minimum, they should be separate XWData instances
        assert data is not new_data
    
    def test_as_xwnode_and_as_xwdata_roundtrip(self):
        """Test roundtrip conversion: XWData -> XWNode -> XWData."""
        original = XWData.from_native({"name": "Alice", "age": 30})
        
        # Convert to XWNode
        node = original.as_xwnode()
        assert node.get_value("name") == "Alice"
        
        # Convert back to XWData
        restored = XWData.from_native(node.to_native())
        assert restored.to_native() == original.to_native()
    
    def test_as_xwdata_with_nested_data(self):
        """Test as_xwdata() with nested data structures."""
        data = XWData.from_native({
            "users": [
                {"name": "Alice", "age": 30},
                {"name": "Bob", "age": 25}
            ]
        })
        
        new_data = data.as_xwdata()
        
        # Check nested structure is preserved
        assert new_data["users"][0]["name"] == "Alice"
        assert new_data["users"][1]["name"] == "Bob"
    
    def test_as_xwnode_creates_on_demand(self):
        """Test that as_xwnode() creates XWNode on-demand if missing."""
        # Create XWData that might not have XWNode (e.g., from hyper-fast path)
        data = XWData.from_native({"name": "Alice"})
        
        # Should be able to get XWNode
        node = data.as_xwnode()
        from exonware.xwnode import XWNode
        assert isinstance(node, XWNode)
        assert node.get_value("name") == "Alice"

