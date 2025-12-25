#!/usr/bin/env python3
"""
#exonware/xwdata/tests/0.core/conftest.py

Core test fixtures.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.3
Generation Date: 26-Oct-2025
"""

import pytest
from pathlib import Path


@pytest.fixture
def core_data_dir():
    """Get core test data directory."""
    return Path(__file__).parent / "data"

