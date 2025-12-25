#!/usr/bin/env python3
"""
#exonware/xwdata/tests/conftest.py

Pytest configuration and fixtures for xwdata tests.
Provides reusable test data and setup utilities.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.3
Generation Date: 26-Oct-2025
"""

import pytest
from pathlib import Path
import sys

# Ensure src is in path for imports
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


@pytest.fixture
def simple_dict_data():
    """Simple dictionary test data."""
    return {
        'name': 'Alice',
        'age': 30,
        'city': 'New York',
        'active': True
    }


@pytest.fixture
def nested_data():
    """Complex nested hierarchical test data."""
    return {
        'users': [
            {
                'id': 1,
                'name': 'Alice',
                'profile': {
                    'email': 'alice@example.com',
                    'preferences': {'theme': 'dark'}
                }
            },
            {
                'id': 2,
                'name': 'Bob',
                'profile': {
                    'email': 'bob@example.com',
                    'preferences': {'theme': 'light'}
                }
            }
        ],
        'metadata': {
            'version': 1.0,
            'created': '2024-01-01'
        }
    }


@pytest.fixture
def test_data_dir():
    """Get the test data directory."""
    return Path(__file__).parent / "0.core" / "data"


@pytest.fixture
def temp_test_dir(tmp_path):
    """Create a temporary directory for test files."""
    test_dir = tmp_path / "test_data"
    test_dir.mkdir()
    return test_dir


@pytest.fixture
def simple_data():
    """Simple data for basic tests."""
    return {"key": "value", "number": 42, "boolean": True}


@pytest.fixture
def json_data():
    """JSON test data."""
    return {
        "name": "Test",
        "config": {
            "timeout": 30,
            "retries": 3
        },
        "items": [1, 2, 3]
    }


@pytest.fixture
def xml_data():
    """XML test data (as dict representation)."""
    return {
        "@id": "1",
        "@href": "test.xml",
        "item": {
            "_text": "content",
            "@attr": "value"
        }
    }


@pytest.fixture
def yaml_data():
    """YAML test data."""
    return {
        "database": {
            "host": "localhost",
            "port": 5432
        },
        "cache": {
            "enabled": True,
            "ttl": 3600
        }
    }

