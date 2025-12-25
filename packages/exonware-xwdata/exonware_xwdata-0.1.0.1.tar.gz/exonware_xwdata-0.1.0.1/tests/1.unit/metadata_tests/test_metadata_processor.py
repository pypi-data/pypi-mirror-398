#!/usr/bin/env python3
"""
#exonware/xwdata/tests/1.unit/metadata_tests/test_metadata_processor.py

Unit tests for MetadataProcessor - metadata application strategies.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.5
Generation Date: 26-Oct-2025
"""

import pytest
from exonware.xwdata.data.metadata.processor import MetadataProcessor
from exonware.xwdata.data.strategies.json import JSONFormatStrategy
from exonware.xwdata.data.strategies.xml import XMLFormatStrategy
from exonware.xwdata.data.strategies.yaml import YAMLFormatStrategy
from exonware.xwdata.config import XWDataConfig


@pytest.mark.xwdata_unit
class TestMetadataProcessorApply:
    """Test metadata application strategies."""
    
    @pytest.mark.asyncio
    async def test_apply_with_no_metadata_returns_data_unchanged(self):
        """Test that applying empty metadata returns data unchanged."""
        processor = MetadataProcessor()
        data = {"key": "value"}
        
        result = await processor.apply(data, {}, "json")
        
        assert result == data
    
    @pytest.mark.asyncio
    async def test_apply_schema_uri_for_json(self):
        """Test applying schema URI for JSON format."""
        processor = MetadataProcessor()
        data = {"key": "value"}
        metadata = {"schema_uri": "http://example.com/schema.json"}
        
        result = await processor.apply(data, metadata, "json")
        
        assert result["$schema"] == "http://example.com/schema.json"
        assert result["key"] == "value"
    
    @pytest.mark.asyncio
    async def test_apply_schema_uri_for_yaml(self):
        """Test applying schema URI for YAML format."""
        processor = MetadataProcessor()
        data = {"key": "value"}
        metadata = {"schema_uri": "http://example.com/schema.json"}
        
        result = await processor.apply(data, metadata, "yaml")
        
        assert result["$schema"] == "http://example.com/schema.json"
        assert result["key"] == "value"
    
    @pytest.mark.asyncio
    async def test_apply_schema_uri_for_xml(self):
        """Test applying schema URI for XML format."""
        processor = MetadataProcessor()
        data = {"root": {"key": "value"}}
        metadata = {"schema_uri": "http://example.com/schema.xsd"}
        
        result = await processor.apply(data, metadata, "xml")
        
        assert "_attributes" in result
        assert result["_attributes"]["xsi:schemaLocation"] == "http://example.com/schema.xsd"
    
    @pytest.mark.asyncio
    async def test_apply_reserved_keys_preserves_existing(self):
        """Test that reserved keys are preserved."""
        processor = MetadataProcessor()
        data = {"$schema": "http://example.com/schema.json", "key": "value"}
        metadata = {"reserved_keys": ["$schema"]}
        
        result = await processor.apply(data, metadata, "json")
        
        assert result["$schema"] == "http://example.com/schema.json"
        assert result["key"] == "value"
    
    @pytest.mark.asyncio
    async def test_apply_type_hints_stores_in_metadata(self):
        """Test applying type hints stores them in metadata."""
        processor = MetadataProcessor()
        data = {"name": "Alice", "age": 30}
        metadata = {"type_hints": {"name": "string", "age": "integer"}}
        
        result = await processor.apply(data, metadata, "json")
        
        assert "_type_hints" in result
        assert result["_type_hints"]["name"] == "string"
        assert result["_type_hints"]["age"] == "integer"
    
    @pytest.mark.asyncio
    async def test_apply_format_specific_metadata_for_json(self):
        """Test applying format-specific metadata for JSON."""
        processor = MetadataProcessor()
        data = {"key": "value"}
        metadata = {"format_specific": {"$id": "test-id", "@context": "http://example.com/context"}}
        
        result = await processor.apply(data, metadata, "json")
        
        assert result["$id"] == "test-id"
        assert result["@context"] == "http://example.com/context"
    
    @pytest.mark.asyncio
    async def test_apply_format_specific_metadata_for_xml(self):
        """Test applying format-specific metadata for XML."""
        processor = MetadataProcessor()
        data = {"root": {"key": "value"}}
        metadata = {"format_specific": {"@xmlns": "http://example.com/ns"}}
        
        result = await processor.apply(data, metadata, "xml")
        
        assert "_attributes" in result
        assert result["_attributes"]["xmlns"] == "http://example.com/ns"
    
    @pytest.mark.asyncio
    async def test_apply_with_unknown_format_returns_unchanged(self):
        """Test that unknown format returns data unchanged."""
        processor = MetadataProcessor()
        data = {"key": "value"}
        metadata = {"schema_uri": "http://example.com/schema.json"}
        
        result = await processor.apply(data, metadata, "unknown_format")
        
        assert result == data


@pytest.mark.xwdata_unit
class TestMetadataProcessorExtract:
    """Test metadata extraction."""
    
    @pytest.mark.asyncio
    async def test_extract_with_disabled_metadata_returns_empty(self):
        """Test that extraction returns empty when disabled."""
        config = XWDataConfig()
        config.metadata.enable_universal_metadata = False
        processor = MetadataProcessor(config)
        strategy = JSONFormatStrategy()
        
        result = await processor.extract({"key": "value"}, strategy)
        
        assert result == {}
    
    @pytest.mark.asyncio
    async def test_extract_with_json_strategy(self):
        """Test metadata extraction using JSON strategy."""
        processor = MetadataProcessor()
        strategy = JSONFormatStrategy()
        data = {"$schema": "http://example.com/schema.json", "@context": "http://example.com/context"}
        
        result = await processor.extract(data, strategy)
        
        assert "format" in result
        assert result["format"] == "json"
        assert "has_schema" in result or "reserved_keys" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

