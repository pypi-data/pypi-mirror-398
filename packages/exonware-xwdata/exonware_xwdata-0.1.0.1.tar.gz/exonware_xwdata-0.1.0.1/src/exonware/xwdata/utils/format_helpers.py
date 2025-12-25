#!/usr/bin/env python3
"""
#exonware/xwdata/src/exonware/xwdata/utils/format_helpers.py

Format detection and serializer helpers for V8.

Performance-first design:
- Fast path for 6 core formats (JSON, YAML, XML, TOML, CSV, BSON)
- Fallback support for 24+ other formats
- Zero overhead for common cases

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 29-Oct-2025
"""

from pathlib import Path
from typing import Optional, Union
from exonware.xwsystem import get_logger

logger = get_logger(__name__)


# ==============================================================================
# FAST FORMAT DETECTION (O(1) Lookup)
# ==============================================================================

# Performance-optimized extension cache for 6 core formats
_CORE_FORMAT_EXTENSIONS = {
    '.json': 'JSON',
    '.yaml': 'YAML',
    '.yml': 'YAML',
    '.xml': 'XML',
    '.toml': 'TOML',
    '.csv': 'CSV',
    '.bson': 'BSON',
}


def detect_format_fast(path: Union[str, Path]) -> Optional[str]:
    """
    Fast format detection for core formats (V8).
    
    Uses O(1) dictionary lookup for maximum performance.
    
    Args:
        path: File path
    
    Returns:
        Format name (uppercase) or None if not a core format
    """
    path_obj = Path(path)
    ext = path_obj.suffix.lower()
    return _CORE_FORMAT_EXTENSIONS.get(ext)


def is_core_format(format_name: str) -> bool:
    """
    Check if format is one of the 6 core optimized formats.
    
    Core formats (fast path):
    - JSON, YAML, XML, TOML, CSV, BSON
    
    Args:
        format_name: Format name
    
    Returns:
        True if core format
    """
    core_formats = {'JSON', 'YAML', 'XML', 'TOML', 'CSV', 'BSON'}
    return format_name.upper() in core_formats


# ==============================================================================
# SERIALIZER FACTORY (Performance-First)
# ==============================================================================

def get_serializer_for_format(format_name: str, fast_path: bool = True):
    """
    Get serializer for format with performance optimization (V8).
    
    Performance strategy:
    1. Fast path for 6 core formats (direct import, zero overhead)
    2. Fallback to AutoSerializer for other 24+ formats
    
    Args:
        format_name: Format name (uppercase)
        fast_path: Use fast path for core formats (default: True)
    
    Returns:
        Serializer instance
    """
    format_upper = format_name.upper()
    
    # FAST PATH: Core formats (direct import, no overhead)
    if fast_path and is_core_format(format_upper):
        if format_upper == 'JSON':
            from exonware.xwsystem.serialization import JsonSerializer
            return JsonSerializer()
        elif format_upper == 'YAML':
            from exonware.xwsystem.serialization import YamlSerializer
            return YamlSerializer()
        elif format_upper == 'XML':
            from exonware.xwsystem.serialization import XmlSerializer
            return XmlSerializer()
        elif format_upper == 'TOML':
            from exonware.xwsystem.serialization import TomlSerializer
            return TomlSerializer()
        elif format_upper == 'CSV':
            from exonware.xwsystem.serialization import CsvSerializer
            return CsvSerializer()
        elif format_upper == 'BSON':
            from exonware.xwsystem.serialization import BsonSerializer
            return BsonSerializer()
    
    # FALLBACK: Other formats (use AutoSerializer)
    logger.debug(f"Using AutoSerializer for {format_upper} (not a core format)")
    from exonware.xwsystem.serialization import AutoSerializer
    return AutoSerializer(default_format=format_upper)


def get_serializer_for_path(path: Union[str, Path], fast_path: bool = True):
    """
    Get serializer for file path with performance optimization (V8).
    
    Performance strategy:
    1. Detect format from extension (O(1))
    2. Use fast path for core formats
    3. Fallback to AutoSerializer for others
    
    Args:
        path: File path
        fast_path: Use fast path for core formats (default: True)
    
    Returns:
        Serializer instance
    """
    # Fast format detection
    format_name = detect_format_fast(path)
    
    if format_name:
        # Core format detected - use fast path
        return get_serializer_for_format(format_name, fast_path=fast_path)
    else:
        # Non-core format - use AutoSerializer
        logger.debug(f"Non-core format for {path}, using AutoSerializer")
        from exonware.xwsystem.serialization import AutoSerializer
        return AutoSerializer()


# ==============================================================================
# FORMAT CAPABILITY DETECTION
# ==============================================================================

def supports_partial_access(format_name: str) -> bool:
    """
    Check if format supports partial access (V8).
    
    Args:
        format_name: Format name
    
    Returns:
        True if format supports get_at/set_at
    """
    # All core formats support partial access
    if is_core_format(format_name):
        return True
    
    # Check format capabilities
    try:
        serializer = get_serializer_for_format(format_name, fast_path=False)
        from exonware.xwsystem.serialization.defs import SerializationCapability
        return SerializationCapability.PARTIAL_ACCESS in serializer.capabilities()
    except Exception:
        return False


def supports_canonical(format_name: str) -> bool:
    """
    Check if format supports canonical serialization (V8).
    
    Args:
        format_name: Format name
    
    Returns:
        True if format supports canonicalize/hash_stable
    """
    # All core formats support canonical
    if is_core_format(format_name):
        return True
    
    # Check format capabilities
    try:
        serializer = get_serializer_for_format(format_name, fast_path=False)
        from exonware.xwsystem.serialization.defs import SerializationCapability
        return SerializationCapability.CANONICAL in serializer.capabilities()
    except Exception:
        return False


def supports_streaming(format_name: str) -> bool:
    """
    Check if format supports streaming (V8).
    
    Args:
        format_name: Format name
    
    Returns:
        True if format supports iter_serialize/iter_deserialize
    """
    # All formats support basic streaming
    try:
        serializer = get_serializer_for_format(format_name, fast_path=False)
        return serializer.supports_streaming()
    except Exception:
        return False

