#!/usr/bin/env python3
"""
#exonware/xwdata/tests/1.unit/builder_tests/test_builder_metadata_config.py

Unit tests for XWDataBuilder metadata and config application.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.5
Generation Date: 26-Oct-2025
"""

import pytest
from exonware.xwdata.builder import XWDataBuilder
from exonware.xwdata import XWData
from exonware.xwdata.config import XWDataConfig


@pytest.mark.xwdata_unit
class TestBuilderMetadata:
    """Test metadata application in builder."""
    
    def test_build_with_metadata_applies_to_xwdata(self):
        """Test that metadata set in builder is applied to XWData."""
        builder = (XWDataBuilder()
                  .set("name", "Alice")
                  .set_metadata("source", "test")
                  .set_metadata("version", "1.0"))
        
        result = builder.build()
        
        assert isinstance(result, XWData)
        metadata = result.get_metadata()
        assert metadata.get("source") == "test"
        assert metadata.get("version") == "1.0"
    
    def test_build_with_multiple_metadata_keys(self):
        """Test building with multiple metadata keys."""
        builder = (XWDataBuilder({"data": "value"})
                  .set_metadata("key1", "value1")
                  .set_metadata("key2", "value2")
                  .set_metadata("key3", "value3"))
        
        result = builder.build()
        metadata = result.get_metadata()
        
        assert metadata.get("key1") == "value1"
        assert metadata.get("key2") == "value2"
        assert metadata.get("key3") == "value3"
    
    def test_set_metadata_is_chainable(self):
        """Test that set_metadata returns self for chaining."""
        builder = XWDataBuilder()
        result = builder.set_metadata("key", "value")
        
        assert result is builder
        assert builder._metadata["key"] == "value"


@pytest.mark.xwdata_unit
class TestBuilderConfig:
    """Test config application in builder."""
    
    def test_build_with_config_applies_to_xwdata(self):
        """Test that config set in builder is applied to XWData."""
        config = XWDataConfig.strict()
        builder = (XWDataBuilder({"name": "Alice"})
                  .with_config(config))
        
        result = builder.build()
        
        assert isinstance(result, XWData)
        # Verify config is applied by checking config-dependent behavior
        assert result._config is not None
    
    def test_with_config_is_chainable(self):
        """Test that with_config returns self for chaining."""
        builder = XWDataBuilder()
        config = XWDataConfig.default()
        result = builder.with_config(config)
        
        assert result is builder
        assert builder._config is config
    
    def test_build_with_custom_config_preserves_settings(self):
        """Test that custom config settings are preserved."""
        config = XWDataConfig.fast()
        builder = (XWDataBuilder({"data": "value"})
                  .with_config(config))
        
        result = builder.build()
        
        # Verify fast config settings are applied
        assert result._config.performance.enable_fast_path is True
    
    def test_build_with_config_and_metadata_works_together(self):
        """Test that both config and metadata can be applied together."""
        config = XWDataConfig.default()
        builder = (XWDataBuilder({"name": "Alice"})
                  .set_metadata("source", "test")
                  .with_config(config))
        
        result = builder.build()
        
        assert isinstance(result, XWData)
        metadata = result.get_metadata()
        assert metadata.get("source") == "test"
        assert result._config is not None


@pytest.mark.xwdata_unit
class TestBuilderMetadataAndData:
    """Test builder with metadata and data together."""
    
    def test_build_preserves_data_when_applying_metadata(self):
        """Test that data is preserved when metadata is applied."""
        builder = (XWDataBuilder({"name": "Alice", "age": 30})
                  .set_metadata("source", "test"))
        
        result = builder.build()
        native = result.to_native()
        
        assert native["name"] == "Alice"
        assert native["age"] == 30
    
    def test_build_metadata_does_not_interfere_with_data(self):
        """Test that metadata doesn't interfere with actual data."""
        builder = (XWDataBuilder({"$schema": "http://example.com/schema"})
                  .set_metadata("schema_version", "1.0"))
        
        result = builder.build()
        native = result.to_native()
        metadata = result.get_metadata()
        
        # Data key should be in native
        assert "$schema" in native
        # Metadata should be separate
        assert metadata.get("schema_version") == "1.0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

