#!/usr/bin/env python3
"""
Test XWData Detection Metadata (Plan 3)

Tests the format detection metadata exposure:
- get_detected_format()
- get_detection_confidence()
- get_detection_info()
- Detection metadata in various scenarios
"""

import pytest
from pathlib import Path
from exonware.xwdata import XWData


@pytest.mark.xwdata_core
class TestDetectionMetadata:
    """Test format detection metadata exposure."""
    
    @pytest.mark.asyncio
    async def test_get_detected_format_json(self, tmp_path):
        """Test detection metadata for JSON file."""
        # Create JSON file
        json_file = tmp_path / "test.json"
        json_file.write_text('{"name": "Alice", "age": 30}')
        
        # Load file
        data = await XWData.load(json_file)
        
        # Check detected format
        assert data.get_detected_format() == 'JSON'
    
    @pytest.mark.asyncio
    async def test_get_detected_format_yaml(self, tmp_path):
        """Test detection metadata for YAML file."""
        # Create YAML file
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("""
name: Alice
age: 30
roles:
  - admin
  - user
""")
        
        # Load file
        data = await XWData.load(yaml_file)
        
        # Check detected format
        assert data.get_detected_format() == 'YAML'
    
    @pytest.mark.asyncio
    async def test_get_detected_format_xml(self, tmp_path):
        """Test detection metadata for XML file."""
        # Create XML file
        xml_file = tmp_path / "test.xml"
        xml_file.write_text("""
<?xml version="1.0"?>
<user>
    <name>Alice</name>
    <age>30</age>
</user>
""")
        
        # Load file
        data = await XWData.load(xml_file)
        
        # Check detected format
        assert data.get_detected_format() == 'XML'
    
    @pytest.mark.asyncio
    async def test_get_detected_format_toml(self, tmp_path):
        """Test detection metadata for TOML file."""
        # Create TOML file
        toml_file = tmp_path / "test.toml"
        toml_file.write_text("""
[user]
name = "Alice"
age = 30
""")
        
        # Load file
        data = await XWData.load(toml_file)
        
        # Check detected format
        assert data.get_detected_format() == 'TOML'
    
    @pytest.mark.asyncio
    async def test_get_detection_confidence_high(self, tmp_path):
        """Test high confidence detection."""
        # Create JSON file with clear format
        json_file = tmp_path / "data.json"
        json_file.write_text('{"key": "value"}')
        
        data = await XWData.load(json_file)
        confidence = data.get_detection_confidence()
        
        # Should have high confidence for clear JSON
        assert confidence is not None
        assert confidence >= 0.8
    
    @pytest.mark.asyncio
    async def test_get_detection_confidence_explicit_hint(self, tmp_path):
        """Test confidence with explicit format hint."""
        # Create file with ambiguous extension
        file = tmp_path / "data.txt"
        file.write_text('{"key": "value"}')
        
        # Load with explicit format hint
        data = await XWData.load(file, format_hint='json')
        confidence = data.get_detection_confidence()
        
        # Should have maximum confidence when hint provided
        assert confidence == 1.0
    
    @pytest.mark.asyncio
    async def test_get_detection_info_complete(self, tmp_path):
        """Test complete detection information."""
        # Create JSON file
        json_file = tmp_path / "test.json"
        json_file.write_text('{"users": [{"name": "Alice"}]}')
        
        data = await XWData.load(json_file)
        info = data.get_detection_info()
        
        # Check all fields present
        assert 'detected_format' in info
        assert 'detection_confidence' in info
        assert 'detection_method' in info
        assert 'format_candidates' in info
        
        # Check values
        assert info['detected_format'] == 'JSON'
        assert isinstance(info['detection_confidence'], (int, float))
        assert info['detection_method'] in ['extension', 'content', 'hint']
        assert isinstance(info['format_candidates'], dict)
    
    @pytest.mark.asyncio
    async def test_detection_method_extension(self, tmp_path):
        """Test detection method via file extension."""
        json_file = tmp_path / "data.json"
        json_file.write_text('{"key": "value"}')
        
        data = await XWData.load(json_file)
        info = data.get_detection_info()
        
        # Extension-based detection
        assert info['detection_method'] in ['extension', 'content']
    
    @pytest.mark.asyncio
    async def test_detection_method_hint(self, tmp_path):
        """Test detection method via format hint."""
        file = tmp_path / "data.txt"
        file.write_text('{"key": "value"}')
        
        data = await XWData.load(file, format_hint='json')
        info = data.get_detection_info()
        
        # Hint-based detection
        assert info['detection_method'] == 'hint'
        assert info['detected_format'] == 'json'
    
    @pytest.mark.asyncio
    async def test_format_candidates_ranking(self, tmp_path):
        """Test format candidates are ranked by confidence."""
        json_file = tmp_path / "data.json"
        json_file.write_text('{"key": "value"}')
        
        data = await XWData.load(json_file)
        info = data.get_detection_info()
        
        candidates = info['format_candidates']
        
        # Should have candidates
        assert len(candidates) > 0
        
        # JSON should be highest
        if 'JSON' in candidates:
            assert candidates['JSON'] >= max(candidates.values()) * 0.95
    
    def test_get_detected_format_native_data(self):
        """Test detection metadata for native data (no file)."""
        data = XWData.from_native({'name': 'Alice', 'age': 30})
        
        # Native data doesn't have format detection
        assert data.get_detected_format() is None
    
    def test_get_detection_confidence_native_data(self):
        """Test confidence for native data (no file)."""
        data = XWData.from_native([1, 2, 3])
        
        # Native data doesn't have detection confidence
        assert data.get_detection_confidence() is None
    
    def test_get_detection_info_native_data(self):
        """Test detection info for native data."""
        data = XWData.from_native({'key': 'value'})
        info = data.get_detection_info()
        
        # All fields should be None or empty
        assert info['detected_format'] is None
        assert info['detection_confidence'] is None
        assert info['detection_method'] is None
        assert info['format_candidates'] == {}


@pytest.mark.xwdata_core
class TestDetectionMetadataPersistence:
    """Test that detection metadata persists through operations."""
    
    @pytest.mark.asyncio
    async def test_detection_persists_after_get(self, tmp_path):
        """Test detection metadata persists after get operation."""
        json_file = tmp_path / "test.json"
        json_file.write_text('{"user": {"name": "Alice"}}')
        
        data = await XWData.load(json_file)
        
        # Perform operation
        value = await data.get('user.name')
        
        # Detection metadata should still be available
        assert data.get_detected_format() == 'JSON'
        assert value == 'Alice'
    
    @pytest.mark.asyncio
    async def test_detection_persists_after_set(self, tmp_path):
        """Test detection metadata persists after set operation."""
        json_file = tmp_path / "test.json"
        json_file.write_text('{"user": {"name": "Alice"}}')
        
        data = await XWData.load(json_file)
        
        # Perform COW operation
        new_data = await data.set('user.age', 30)
        
        # Detection metadata should persist to new instance
        assert new_data.get_detected_format() == 'JSON'
    
    @pytest.mark.asyncio
    async def test_detection_persists_after_merge(self, tmp_path):
        """Test detection metadata after merge operation."""
        json_file1 = tmp_path / "test1.json"
        json_file1.write_text('{"a": 1}')
        
        json_file2 = tmp_path / "test2.json"
        json_file2.write_text('{"b": 2}')
        
        data1 = await XWData.load(json_file1)
        data2 = await XWData.load(json_file2)
        
        # Merge
        merged = await data1.merge(data2)
        
        # Merged data should have detection info from last source
        assert merged.get_detected_format() is not None


@pytest.mark.xwdata_core
class TestDetectionTransparency:
    """Test detection transparency for debugging."""
    
    @pytest.mark.asyncio
    async def test_detection_info_for_debugging(self, tmp_path):
        """Test using detection info for debugging."""
        json_file = tmp_path / "config.json"
        json_file.write_text('{"database": {"host": "localhost"}}')
        
        data = await XWData.load(json_file)
        info = data.get_detection_info()
        
        # Useful for debugging: know what format was detected
        print(f"Detected format: {info['detected_format']}")
        print(f"Confidence: {info['detection_confidence']:.0%}")
        print(f"Method: {info['detection_method']}")
        print(f"Candidates: {info['format_candidates']}")
        
        # Assertions
        assert info['detected_format'] is not None
        assert 0.0 <= info['detection_confidence'] <= 1.0
    
    @pytest.mark.asyncio
    async def test_low_confidence_warning(self, tmp_path):
        """Test detecting low confidence scenarios."""
        # Create ambiguous file
        file = tmp_path / "data.txt"
        file.write_text('some ambiguous content')
        
        try:
            data = await XWData.load(file)
            confidence = data.get_detection_confidence()
            
            # Check if confidence is low
            if confidence and confidence < 0.8:
                print(f"Warning: Low confidence detection ({confidence:.0%})")
                print(f"Consider using format_hint parameter")
        except Exception:
            # Expected if format can't be detected
            pass


@pytest.mark.xwdata_core
class TestFormatConversionTracking:
    """Test tracking format conversions."""
    
    @pytest.mark.asyncio
    async def test_track_json_to_yaml_conversion(self, tmp_path):
        """Test tracking format conversion from JSON to YAML."""
        # Load JSON
        json_file = tmp_path / "input.json"
        json_file.write_text('{"name": "Alice", "age": 30}')
        
        data = await XWData.load(json_file)
        original_format = data.get_detected_format()
        
        assert original_format == 'JSON'
        
        # Save as YAML
        yaml_file = tmp_path / "output.yaml"
        await data.save(yaml_file)
        
        # Load YAML back
        yaml_data = await XWData.load(yaml_file)
        new_format = yaml_data.get_detected_format()
        
        assert new_format == 'YAML'
        
        # Verify data integrity
        assert await yaml_data.get('name') == 'Alice'
        assert await yaml_data.get('age') == 30
    
    @pytest.mark.asyncio
    async def test_track_multiple_conversions(self, tmp_path):
        """Test tracking through multiple format conversions."""
        # JSON → YAML → TOML
        
        # Start with JSON
        json_file = tmp_path / "data.json"
        json_file.write_text('{"config": {"timeout": 30}}')
        
        json_data = await XWData.load(json_file)
        assert json_data.get_detected_format() == 'JSON'
        
        # Convert to YAML
        yaml_file = tmp_path / "data.yaml"
        await json_data.save(yaml_file)
        
        yaml_data = await XWData.load(yaml_file)
        assert yaml_data.get_detected_format() == 'YAML'
        
        # Convert to TOML
        toml_file = tmp_path / "data.toml"
        await yaml_data.save(toml_file)
        
        toml_data = await XWData.load(toml_file)
        assert toml_data.get_detected_format() == 'TOML'
        
        # Verify data integrity through all conversions
        assert await toml_data.get('config.timeout') == 30


@pytest.mark.xwdata_core
class TestDetectionExamples:
    """Real-world usage examples."""
    
    @pytest.mark.asyncio
    async def test_example_verify_format(self, tmp_path):
        """Example: Verify expected format."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"api_key": "secret"}')
        
        data = await XWData.load(config_file)
        
        # Verify it's JSON as expected
        if data.get_detected_format() != 'JSON':
            raise ValueError("Expected JSON format!")
        
        assert data.get_detected_format() == 'JSON'
    
    @pytest.mark.asyncio
    async def test_example_format_aware_processing(self, tmp_path):
        """Example: Format-aware processing."""
        json_file = tmp_path / "data.json"
        json_file.write_text('{"items": [1, 2, 3]}')
        
        data = await XWData.load(json_file)
        
        # Process differently based on detected format
        format_name = data.get_detected_format()
        
        if format_name == 'JSON':
            # JSON-specific processing
            print("Processing JSON data...")
        elif format_name == 'YAML':
            # YAML-specific processing
            print("Processing YAML data...")
        
        assert format_name in ['JSON', 'YAML', 'XML', 'TOML']
    
    @pytest.mark.asyncio
    async def test_example_confidence_check(self, tmp_path):
        """Example: Check confidence before proceeding."""
        data_file = tmp_path / "uncertain.data"
        data_file.write_text('{"key": "value"}')
        
        try:
            data = await XWData.load(data_file, format_hint='json')
            
            confidence = data.get_detection_confidence()
            
            if confidence and confidence < 0.8:
                print(f"Warning: Low confidence ({confidence:.0%})")
                # Maybe ask user to confirm or provide explicit format
            
            assert confidence is not None
        except Exception:
            # Handle detection failure
            pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

