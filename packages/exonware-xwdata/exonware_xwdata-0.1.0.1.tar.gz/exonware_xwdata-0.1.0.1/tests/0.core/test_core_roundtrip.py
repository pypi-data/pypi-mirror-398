#!/usr/bin/env python3
"""
#exonware/xwdata/tests/0.core/test_core_roundtrip.py

Core roundtrip tests for XWData using xwsystem serializers.

Company: eXonware.com
Author:   Eng. Muhammad AlShehri
Email:    connect@exonware.com
Version:  0.0.1
Generation Date: 15-Dec-2025
"""

from pathlib import Path

import pytest

from exonware.xwdata import XWData


SIMPLE_PAYLOAD = {
    "name": "example",
    "active": True,
    "count": 3,
    "items": [
        {"id": 1, "value": "a"},
        {"id": 2, "value": "b"},
    ],
}


def _normalize_for_xml(value):
    """
    Normalize Python data to a stringly-typed representation for XML comparison.

    XML serializers often represent everything as strings, so for XML roundtrips
    we compare against a string-normalized version of the original payload.
    """
    if isinstance(value, dict):
        return {k: _normalize_for_xml(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize_for_xml(v) for v in value]
    if isinstance(value, bool):
        # Most XML serializers use lowercase true/false
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return value


@pytest.mark.xwdata_core
@pytest.mark.asyncio
@pytest.mark.parametrize("fmt,ext", [
    ("json", ".json"),
    ("yaml", ".yaml"),
    ("toml", ".toml"),
    ("xml", ".xml"),
])
async def test_roundtrip_memory_to_string_and_back(fmt, ext):
    """
    In-memory roundtrip: from_native -> serialize -> parse -> to_native.

    This verifies that for core text formats, XWData + xwsystem can serialize
    and deserialize without losing information for simple structures.
    """
    data = XWData.from_native(SIMPLE_PAYLOAD)

    # 1. Serialize to target format
    serialized = await data.serialize(fmt)
    assert isinstance(serialized, (str, bytes))

    # 2. Parse back into XWData
    parsed = await XWData.parse(serialized, fmt)

    # 3. Native structures should match
    assert parsed.to_native() == SIMPLE_PAYLOAD


@pytest.mark.xwdata_core
@pytest.mark.asyncio
@pytest.mark.parametrize("fmt,ext", [
    ("json", ".json"),
    ("yaml", ".yaml"),
    ("toml", ".toml"),
    ("xml", ".xml"),
])
async def test_roundtrip_file_save_load(tmp_path, fmt, ext):
    """
    File-based roundtrip: from_native -> save -> load -> to_native.

    This exercises the full XWData pipeline (engine.save + engine.load) and
    ensures that the persisted representation can be read back correctly.
    """
    dest: Path = tmp_path / f"roundtrip{ext}"

    # 1. Create data and save to file
    data = XWData.from_native(SIMPLE_PAYLOAD)
    await data.save(dest, format=fmt)
    assert dest.exists()
    assert dest.stat().st_size > 0

    # 2. Load from file
    loaded = await XWData.load(dest)

    # 3. Native structures should be equal (with XML using stringly-typed values)
    loaded_native = loaded.to_native()
    if fmt == "xml":
        assert loaded_native == _normalize_for_xml(SIMPLE_PAYLOAD)
    else:
        assert loaded_native == SIMPLE_PAYLOAD


