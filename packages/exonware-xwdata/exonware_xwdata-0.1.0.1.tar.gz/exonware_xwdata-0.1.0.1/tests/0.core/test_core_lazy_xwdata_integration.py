#!/usr/bin/env python3
"""
#exonware/xwdata/tests/0.core/test_core_lazy_xwdata_integration.py

Integration tests for XWData lazy loading, atomic access, and paging.

Company: eXonware.com
Author:   Eng. Muhammad AlShehri
Email:    connect@exonware.com
Version:  0.0.1
Generation Date: 15-Dec-2025
"""

import json
from pathlib import Path

import pytest

from exonware.xwdata import XWData
from exonware.xwdata.config import XWDataConfig


@pytest.mark.xwdata_core
@pytest.mark.asyncio
class TestXWDataLazyFileMode:
    """Verify lazy file-backed behaviour of XWData (atomic get/set + paging)."""

    async def _make_lazy_config(self) -> XWDataConfig:
        """
        Create a config that forces LAZY strategy for small test files.

        We set:
        - thresholds.small_mb = 0.0  (so any non-zero size skips FULL)
        - thresholds.medium_mb = 1000.0 (so normal test files fall into LAZY)
        - lazy.defer_file_io = True  (so engine chooses file-level lazy mode)
        """
        cfg = XWDataConfig.default()
        cfg.thresholds.small_mb = 0.0
        cfg.thresholds.medium_mb = 1000.0
        cfg.lazy.defer_file_io = True
        return cfg

    async def test_lazy_get_uses_atomic_read_when_in_file_mode(self, tmp_path):
        """XWData.get() should use engine.lazy_get_from_file for lazy file-backed data."""
        # Prepare a small JSON file with nested data
        data = {
            "users": [
                {"id": 1, "name": "Alice", "age": 30},
                {"id": 2, "name": "Bob", "age": 40},
            ]
        }
        file_path: Path = tmp_path / "users.json"
        file_path.write_text(json.dumps(data), encoding="utf-8")

        cfg = await self._make_lazy_config()

        # Load with config that forces LAZY strategy
        xw = await XWData.load(file_path, config=cfg)

        # Engine should have created a lazy, file-backed node
        assert xw._metadata.get("lazy_mode") == "file"
        assert xw._metadata.get("source_path") == str(file_path)

        # Access a value via lazy get – this should go through atomic_read_path
        name = await xw.get("users.0.name")
        age = await xw.get("users.1.age")
        assert name == "Alice"
        assert age == 40

    async def test_lazy_set_uses_atomic_update_and_preserves_lazy_mode(self, tmp_path):
        """XWData.set() on lazy file-backed data should prefer atomic path update."""
        original = {"counter": 0, "meta": {"version": 1}}
        file_path: Path = tmp_path / "counter.json"
        file_path.write_text(json.dumps(original), encoding="utf-8")

        cfg = await self._make_lazy_config()
        xw = await XWData.load(file_path, config=cfg)

        assert xw._metadata.get("lazy_mode") == "file"

        # Perform an atomic update
        updated = await xw.set("counter", 5)

        # The returned instance should still be in lazy file mode
        assert updated._metadata.get("lazy_mode") == "file"
        assert updated._metadata.get("source_path") == str(file_path)

        # Re-load the file normally and verify the counter changed on disk
        reloaded = await XWData.load(file_path, config=cfg)
        value = await reloaded.get("counter")
        assert value == 5

    async def test_paging_large_file_backed_dataset(self, tmp_path):
        """XWData.get_page() should page over file-backed lazy data."""
        # Create a simple JSON array file
        records = [{"id": i, "value": f"v{i}"} for i in range(10)]
        file_path: Path = tmp_path / "records.json"
        file_path.write_text(json.dumps(records), encoding="utf-8")

        cfg = await self._make_lazy_config()

        # We still load via XWData.load; detection will treat this as text/JSON,
        # but our lazy strategy will mark it as file-backed lazy.
        xw = await XWData.load(file_path, config=cfg)
        assert xw._metadata.get("lazy_mode") == "file"

        # Request a page of size 3
        page = await xw.get_page(page_number=2, page_size=3)
        assert len(page) == 3

        # Verify contents match the expected slice (records[3:6])
        expected_slice = records[3:6]
        got = [item.to_native() for item in page]
        assert got == expected_slice

    @pytest.mark.asyncio
    async def test_jsonl_uses_specialized_serializer_for_streaming_paging(self, tmp_path):
        """
        Verify that JSONL files use JsonLinesSerializer.get_record_page()
        for efficient streaming paging (line-by-line, no full-file load).
        """
        # Create a JSONL file with many records
        jsonl_file = tmp_path / "records.jsonl"
        records = [{"id": i, "name": f"Record{i}", "value": i * 10} for i in range(100)]
        
        # Write as JSONL (one JSON object per line)
        with jsonl_file.open("w", encoding="utf-8") as f:
            for record in records:
                f.write(json.dumps(record) + "\n")

        cfg = await self._make_lazy_config()

        # Load in lazy mode
        xw = await XWData.load(jsonl_file, config=cfg)
        assert xw._metadata.get("lazy_mode") == "file"
        assert xw._metadata.get("format") == "JSONL"  # Should detect as JSONL

        # Request a page - this should use JsonLinesSerializer.get_record_page()
        # which streams line-by-line without loading the entire file
        page = await xw.get_page(page_number=2, page_size=10)
        assert len(page) == 10

        # Verify we got the correct records (indices 10-19)
        expected_slice = records[10:20]
        got = [item.to_native() for item in page]
        assert got == expected_slice

        # Verify metadata on page items
        for item in page:
            assert item._metadata.get("source_path") == str(jsonl_file)
            assert item._metadata.get("format") == "JSONL"
            assert item._metadata.get("page_number") == 2
            assert item._metadata.get("page_size") == 10


@pytest.mark.xwdata_core
@pytest.mark.asyncio
class TestMultiDocumentYAMLStreaming:
    """Test multi-document YAML streaming support."""
    
    async def test_yaml_multi_document_streaming(self, tmp_path):
        """
        Verify that YAML multi-document files use incremental_load()
        for true streaming (yields documents one at a time).
        """
        # Create a YAML file with multiple documents separated by ---
        yaml_file = tmp_path / "multi_doc.yaml"
        yaml_content = """---
name: Document 1
type: config
values:
  - a
  - b
---
name: Document 2
type: data
items:
  - id: 1
    value: 100
  - id: 2
    value: 200
---
name: Document 3
type: metadata
version: 1.0
"""
        yaml_file.write_text(yaml_content, encoding="utf-8")
        
        # Import engine to test stream_load directly
        from exonware.xwdata.data.engine import XWDataEngine
        from exonware.xwdata.config import XWDataConfig
        
        cfg = XWDataConfig.default()
        engine = XWDataEngine(config=cfg)
        
        # Use stream_load to get documents one at a time
        documents = []
        async for node in engine.stream_load(yaml_file):
            documents.append(node.to_native())
        
        # Verify we got 3 separate documents
        assert len(documents) == 3
        assert documents[0]["name"] == "Document 1"
        assert documents[0]["type"] == "config"
        assert documents[1]["name"] == "Document 2"
        assert documents[1]["type"] == "data"
        assert documents[2]["name"] == "Document 3"
        assert documents[2]["type"] == "metadata"
        
        # Verify each document is independent
        assert "values" in documents[0]
        assert "items" in documents[1]
        assert "version" in documents[2]
    
    async def test_yaml_single_document_fallback(self, tmp_path):
        """
        Verify that single-document YAML files still work correctly
        (should yield one document).
        """
        # Create a single-document YAML file
        yaml_file = tmp_path / "single_doc.yaml"
        yaml_content = """name: Single Document
type: config
values:
  - a
  - b
  - c
"""
        yaml_file.write_text(yaml_content, encoding="utf-8")
        
        from exonware.xwdata.data.engine import XWDataEngine
        from exonware.xwdata.config import XWDataConfig
        
        cfg = XWDataConfig.default()
        engine = XWDataEngine(config=cfg)
        
        # Use stream_load - should yield one document
        documents = []
        async for node in engine.stream_load(yaml_file):
            documents.append(node.to_native())
        
        # Verify we got 1 document
        assert len(documents) == 1
        assert documents[0]["name"] == "Single Document"
        assert documents[0]["type"] == "config"
        assert len(documents[0]["values"]) == 3
    
    async def test_yaml_streaming_via_xwdata(self, tmp_path):
        """
        Test YAML multi-document streaming through XWData.stream_load() if available.
        """
        # Create a YAML file with multiple documents
        yaml_file = tmp_path / "stream_test.yaml"
        yaml_content = """---
id: 1
name: First
---
id: 2
name: Second
---
id: 3
name: Third
"""
        yaml_file.write_text(yaml_content, encoding="utf-8")
        
        # Test via engine directly (XWData.stream_load may not exist yet)
        from exonware.xwdata.data.engine import XWDataEngine
        from exonware.xwdata.config import XWDataConfig
        
        cfg = XWDataConfig.default()
        engine = XWDataEngine(config=cfg)
        
        # Stream load and collect documents
        collected = []
        async for node in engine.stream_load(yaml_file):
            collected.append(node.to_native())
        
        # Verify streaming worked
        assert len(collected) == 3
        assert collected[0]["id"] == 1
        assert collected[1]["id"] == 2
        assert collected[2]["id"] == 3


