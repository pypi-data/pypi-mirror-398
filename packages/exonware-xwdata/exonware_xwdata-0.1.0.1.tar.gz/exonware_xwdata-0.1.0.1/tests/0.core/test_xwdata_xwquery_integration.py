#!/usr/bin/env python3
"""
#exonware/xwdata/tests/0.core/test_xwdata_xwquery_integration.py

Core tests for XWData integration with XWQuery via XWNode.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.4
Generation Date: 08-Nov-2025
"""

import pytest
import asyncio
from exonware.xwdata import XWData


@pytest.mark.xwdata_core
class TestXWDataXWQueryIntegration:
    """Test XWData integration with XWQuery via XWNode."""
    
    @pytest.mark.asyncio
    async def test_as_xwnode_returns_xwnode(self):
        """Test that as_xwnode() returns XWNode instance."""
        data = XWData.from_native({'users': [{'name': 'Alice', 'age': 30}]})
        
        # Get XWNode
        node = data.as_xwnode()
        
        # Verify it's an XWNode
        from exonware.xwnode import XWNode
        assert isinstance(node, XWNode)
        
        # Verify data is accessible
        assert node.get_value('users.0.name') == 'Alice'
    
    @pytest.mark.asyncio
    async def test_query_method_works(self):
        """Test that query() method works (if xwquery is available)."""
        data = XWData.from_native({
            'users': [
                {'name': 'Alice', 'age': 30},
                {'name': 'Bob', 'age': 25},
                {'name': 'Charlie', 'age': 35}
            ]
        })
        
        # Try to use query (may fail if xwquery not installed)
        try:
            result = await data.query("SELECT * FROM users WHERE age > 28", format='sql')
            # If query works, verify results
            assert result is not None
        except ImportError:
            pytest.skip("xwquery not available")
    
    @pytest.mark.asyncio
    async def test_xwnode_navigation_works(self):
        """Test that XWNode navigation works through as_xwnode()."""
        data = XWData.from_native({
            'level1': {
                'level2': {
                    'level3': 'deep_value'
                }
            }
        })
        
        node = data.as_xwnode()
        
        # Test path navigation
        assert node.get_value('level1.level2.level3') == 'deep_value'
        
        # Test direct access
        assert node['level1']['level2']['level3'] == 'deep_value'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

