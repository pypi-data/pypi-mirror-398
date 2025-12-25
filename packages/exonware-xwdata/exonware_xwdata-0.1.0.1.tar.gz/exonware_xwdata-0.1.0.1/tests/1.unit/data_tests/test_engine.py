#!/usr/bin/env python3
"""
#exonware/xwdata/tests/1.unit/data_tests/test_engine.py

Unit tests for XWDataEngine.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.3
Generation Date: 26-Oct-2025
"""

import pytest


@pytest.mark.xwdata_unit
class TestXWDataEngine:
    """Unit tests for XWDataEngine."""
    
    def test_engine_initialization(self):
        """Test engine can be initialized."""
        from exonware.xwdata.data import XWDataEngine
        from exonware.xwdata import XWDataConfig
        
        config = XWDataConfig.default()
        engine = XWDataEngine(config)
        
        assert engine is not None
        assert engine._config is not None
    
    @pytest.mark.asyncio
    async def test_create_node_from_native(self, simple_dict_data):
        """Test creating node from native data."""
        from exonware.xwdata.data import XWDataEngine
        from exonware.xwdata import XWDataConfig
        
        engine = XWDataEngine(XWDataConfig.default())
        node = await engine.create_node_from_native(simple_dict_data)
        
        assert node is not None
        assert node.to_native() == simple_dict_data
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Merge functionality is a stub - implement in future iteration")
    async def test_engine_merge_nodes(self):
        """Test engine can merge nodes."""
        from exonware.xwdata.data import XWDataEngine
        from exonware.xwdata import XWDataConfig
        
        engine = XWDataEngine(XWDataConfig.default())
        
        node1 = await engine.create_node_from_native({'a': 1, 'b': 2})
        node2 = await engine.create_node_from_native({'b': 3, 'c': 4})
        
        merged = await engine.merge_nodes([node1, node2], strategy='deep')
        merged_data = merged.to_native()
        
        assert merged_data['a'] == 1
        assert merged_data['b'] == 3  # Overridden
        assert merged_data['c'] == 4

