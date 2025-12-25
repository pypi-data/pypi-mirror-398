#!/usr/bin/env python3
"""
#exonware/xwdata/tests/2.integration/test_reference_resolution.py

Integration tests for reference resolution in real-world scenarios.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1
Generation Date: 28-Oct-2025
"""

import pytest
import json
from pathlib import Path

from exonware.xwdata import XWData
from exonware.xwdata.config import XWDataConfig


@pytest.mark.xwdata_integration
class TestReferenceIntegration:
    """Integration tests for reference resolution."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_ref_resolution(self, tmp_path):
        """Test complete reference resolution workflow via XWData."""
        # Create multi-file reference chain
        # base.json
        base_data = {
            "id": "base",
            "common": {
                "version": "1.0",
                "author": "Test"
            }
        }
        (tmp_path / "base.json").write_text(json.dumps(base_data))
        
        # user.json (refs base)
        user_data = {
            "type": "user",
            "base": {"$ref": "base.json"},
            "properties": {
                "name": {"type": "string"}
            }
        }
        (tmp_path / "user.json").write_text(json.dumps(user_data))
        
        # main.json (refs user)
        main_data = {
            "schema": {
                "user": {"$ref": "user.json"}
            }
        }
        main_file = tmp_path / "main.json"
        main_file.write_text(json.dumps(main_data))
        
        # Enable reference resolution
        config = XWDataConfig.default()
        config.reference.resolution_mode.name = 'EAGER'
        
        # Load main file
        data = await XWData.load(main_file, config=config)
        
        # Verify complete resolution chain
        native = data.to_native()
        assert native['schema']['user']['type'] == "user"
        assert native['schema']['user']['base']['id'] == "base"
        assert native['schema']['user']['base']['common']['version'] == "1.0"
    
    @pytest.mark.asyncio
    async def test_cross_format_references(self, tmp_path):
        """Test references across different formats (future enhancement)."""
        # For now, test same format
        # Future: JSON refs YAML, etc.
        
        # JSON file with reference
        ref_data = {"value": "referenced"}
        (tmp_path / "ref.json").write_text(json.dumps(ref_data))
        
        main_data = {"data": {"$ref": "ref.json"}}
        main_file = tmp_path / "main.json"
        main_file.write_text(json.dumps(main_data))
        
        config = XWDataConfig.default()
        config.reference.resolution_mode.name = 'EAGER'
        
        data = await XWData.load(main_file, config=config)
        native = data.to_native()
        
        assert native['data']['value'] == "referenced"
    
    @pytest.mark.asyncio
    async def test_openapi_spec_refs(self, tmp_path):
        """Test OpenAPI specification with $refs."""
        # Common definitions file
        definitions = {
            "Error": {
                "type": "object",
                "properties": {
                    "code": {"type": "integer"},
                    "message": {"type": "string"}
                }
            }
        }
        (tmp_path / "definitions.json").write_text(json.dumps(definitions))
        
        # OpenAPI spec with references
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/error": {
                    "get": {
                        "responses": {
                            "404": {
                                "description": "Not found",
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "definitions.json#/Error"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        spec_file = tmp_path / "api.json"
        spec_file.write_text(json.dumps(spec))
        
        config = XWDataConfig.default()
        config.reference.resolution_mode.name = 'EAGER'
        
        data = await XWData.load(spec_file, config=config)
        native = data.to_native()
        
        # Verify reference resolved
        error_schema = native['paths']['/error']['get']['responses']['404']['content']['application/json']['schema']
        assert error_schema['type'] == "object"
        assert 'code' in error_schema['properties']
    
    @pytest.mark.asyncio
    async def test_performance_with_caching(self, tmp_path):
        """Test that caching improves performance with multiple refs."""
        # Create commonly referenced file
        common_data = {"shared": "data", "items": list(range(100))}
        (tmp_path / "common.json").write_text(json.dumps(common_data))
        
        # Create 10 files that all reference common.json
        for i in range(10):
            data = {
                "id": i,
                "common": {"$ref": "common.json"}
            }
            (tmp_path / f"file{i}.json").write_text(json.dumps(data))
        
        # Master file referencing all 10
        master_data = {
            "files": [{"$ref": f"file{i}.json"} for i in range(10)]
        }
        master_file = tmp_path / "master.json"
        master_file.write_text(json.dumps(master_data))
        
        config = XWDataConfig.default()
        config.reference.resolution_mode.name = 'EAGER'
        config.reference.cache_resolved = True
        
        import time
        start = time.time()
        
        data = await XWData.load(master_file, config=config)
        
        elapsed = time.time() - start
        
        # Should complete in reasonable time (< 2 seconds with caching)
        assert elapsed < 2.0
        
        # Verify all resolved
        native = data.to_native()
        assert len(native['files']) == 10
        assert all(f['common']['shared'] == "data" for f in native['files'])
    
    @pytest.mark.asyncio
    async def test_disabled_resolution(self, tmp_path):
        """Test that references are not resolved when disabled."""
        # Create referenced file
        ref_data = {"value": "should not resolve"}
        (tmp_path / "ref.json").write_text(json.dumps(ref_data))
        
        # Main file with reference
        main_data = {"ref": {"$ref": "ref.json"}}
        main_file = tmp_path / "main.json"
        main_file.write_text(json.dumps(main_data))
        
        # Disable resolution
        config = XWDataConfig.default()
        config.reference.resolution_mode.name = 'DISABLED'
        
        data = await XWData.load(main_file, config=config)
        native = data.to_native()
        
        # Reference should remain as-is
        assert native['ref'] == {"$ref": "ref.json"}


@pytest.mark.xwdata_integration
@pytest.mark.xwdata_performance
class TestReferencePerformance:
    """Performance tests for reference resolution."""
    
    @pytest.mark.asyncio
    async def test_large_file_refs(self, tmp_path):
        """Test performance with large referenced files."""
        # Create large data file (1000 items)
        large_data = {
            "items": [{"id": i, "name": f"Item {i}", "data": "x" * 100} for i in range(1000)]
        }
        (tmp_path / "large.json").write_text(json.dumps(large_data))
        
        # Reference it
        main_data = {"dataset": {"$ref": "large.json"}}
        main_file = tmp_path / "main.json"
        main_file.write_text(json.dumps(main_data))
        
        config = XWDataConfig.default()
        config.reference.resolution_mode.name = 'EAGER'
        
        import time
        start = time.time()
        
        data = await XWData.load(main_file, config=config)
        
        elapsed = time.time() - start
        
        # Should complete in reasonable time
        assert elapsed < 5.0
        
        native = data.to_native()
        assert len(native['dataset']['items']) == 1000
    
    @pytest.mark.asyncio
    async def test_deep_nesting_refs(self, tmp_path):
        """Test performance with deeply nested references."""
        # Create chain of 5 references
        for i in range(5, 0, -1):
            if i == 5:
                data = {"level": i, "value": "final"}
            else:
                data = {"level": i, "next": {"$ref": f"level{i+1}.json"}}
            (tmp_path / f"level{i}.json").write_text(json.dumps(data))
        
        config = XWDataConfig.default()
        config.reference.resolution_mode.name = 'EAGER'
        
        import time
        start = time.time()
        
        data = await XWData.load(tmp_path / "level1.json", config=config)
        
        elapsed = time.time() - start
        
        # Should complete quickly
        assert elapsed < 1.0
        
        # Verify complete chain resolved
        native = data.to_native()
        assert native['level'] == 1
        assert native['next']['level'] == 2
        assert native['next']['next']['level'] == 3
        assert native['next']['next']['next']['level'] == 4
        assert native['next']['next']['next']['next']['level'] == 5
        assert native['next']['next']['next']['next']['value'] == "final"

