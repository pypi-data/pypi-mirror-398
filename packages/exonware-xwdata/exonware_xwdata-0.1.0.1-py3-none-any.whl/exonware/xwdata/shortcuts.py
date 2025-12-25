#!/usr/bin/env python3
"""
#exonware/xwdata/src/exonware/xwdata/shortcuts.py

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: October 27, 2025

Shortcuts API for quick data operations.

Provides convenient one-liner functions for common data tasks.

Priority Alignment:
1. Security - Safe shortcuts with validation
2. Usability - Simple, intuitive API  
3. Maintainability - Delegates to core functionality
4. Performance - Efficient shortcuts
5. Extensibility - Easy to add new shortcuts
"""

from typing import Any, Optional, Union
from pathlib import Path


# =============================================================================
# QUICK LOAD/SAVE SHORTCUTS
# =============================================================================

def quick_load(source: Union[str, Path, dict], format: Optional[str] = None) -> 'XWData':
    """
    Quick load from file or dict.
    
    Args:
        source: File path or dictionary
        format: Format (auto-detected if None)
        
    Returns:
        XWData instance
        
    Examples:
        >>> from exonware.xwdata import quick_load
        >>> data = quick_load("config.json")
        >>> data = quick_load({"name": "Alice"})
    """
    from .facade import XWData
    
    if isinstance(source, (str, Path)):
        return XWData.load(source, format=format)
    else:
        return XWData.from_native(source)


def quick_save(data: Any, target: Union[str, Path], format: Optional[str] = None) -> None:
    """
    Quick save to file.
    
    Args:
        data: Data to save (XWData or native)
        target: Target file path
        format: Format (auto-detected from extension if None)
        
    Examples:
        >>> from exonware.xwdata import quick_save
        >>> quick_save({"name": "Alice"}, "user.json")
    """
    from .facade import XWData
    
    if not isinstance(data, XWData):
        data = XWData.from_native(data)
    
    data.save(target, format=format)


# =============================================================================
# QUICK CONVERSION SHORTCUTS
# =============================================================================

def quick_convert(
    source: Union[str, Path, Any],
    target: Union[str, Path],
    source_format: Optional[str] = None,
    target_format: Optional[str] = None
) -> None:
    """
    Quick convert from one format to another.
    
    Args:
        source: Source file or data
        target: Target file path
        source_format: Source format (auto-detected if None)
        target_format: Target format (auto-detected if None)
        
    Examples:
        >>> from exonware.xwdata import quick_convert
        >>> # Convert JSON to YAML
        >>> quick_convert("config.json", "config.yaml")
        >>> # Convert dict to XML file
        >>> quick_convert({"root": {"item": "value"}}, "output.xml")
    """
    data = quick_load(source, format=source_format)
    quick_save(data, target, format=target_format)


def to_json(data: Any, **kwargs) -> str:
    """Quick convert to JSON string."""
    from .facade import XWData
    if not isinstance(data, XWData):
        data = XWData.from_native(data)
    return data.serialize("json", **kwargs)


def to_yaml(data: Any, **kwargs) -> str:
    """Quick convert to YAML string."""
    from .facade import XWData
    if not isinstance(data, XWData):
        data = XWData.from_native(data)
    return data.serialize("yaml", **kwargs)


def to_xml(data: Any, **kwargs) -> str:
    """Quick convert to XML string."""
    from .facade import XWData
    if not isinstance(data, XWData):
        data = XWData.from_native(data)
    return data.serialize("xml", **kwargs)


def to_toml(data: Any, **kwargs) -> str:
    """Quick convert to TOML string."""
    from .facade import XWData
    if not isinstance(data, XWData):
        data = XWData.from_native(data)
    return data.serialize("toml", **kwargs)


def to_csv(data: Any, **kwargs) -> str:
    """Quick convert to CSV string."""
    from .facade import XWData
    if not isinstance(data, XWData):
        data = XWData.from_native(data)
    return data.serialize("csv", **kwargs)


def from_json(json_str: str) -> 'XWData':
    """Quick parse JSON string."""
    from .facade import XWData
    return XWData.parse(json_str, format="json")


def from_yaml(yaml_str: str) -> 'XWData':
    """Quick parse YAML string."""
    from .facade import XWData
    return XWData.parse(yaml_str, format="yaml")


def from_xml(xml_str: str) -> 'XWData':
    """Quick parse XML string."""
    from .facade import XWData
    return XWData.parse(xml_str, format="xml")


def from_toml(toml_str: str) -> 'XWData':
    """Quick parse TOML string."""
    from .facade import XWData
    return XWData.parse(toml_str, format="toml")


def from_csv(csv_str: str) -> 'XWData':
    """Quick parse CSV string."""
    from .facade import XWData
    return XWData.parse(csv_str, format="csv")


# =============================================================================
# QUICK QUERY SHORTCUTS
# =============================================================================

def quick_get(data: Any, path: str, default: Any = None) -> Any:
    """
    Quick get value at path.
    
    Args:
        data: Data to query (XWData or native)
        path: Path to value
        default: Default if not found
        
    Returns:
        Value at path or default
        
    Examples:
        >>> from exonware.xwdata import quick_get
        >>> data = {"user": {"name": "Alice"}}
        >>> quick_get(data, "user.name")  # "Alice"
    """
    from .facade import XWData
    
    if not isinstance(data, XWData):
        data = XWData.from_native(data)
    
    result = data.get(path)
    return result.value if result and result.exists else default


def quick_set(data: Any, path: str, value: Any) -> 'XWData':
    """
    Quick set value at path (returns new XWData with COW).
    
    Args:
        data: Data to modify
        path: Path to set
        value: Value to set
        
    Returns:
        New XWData instance
        
    Examples:
        >>> from exonware.xwdata import quick_set
        >>> data = {"user": {"name": "Alice"}}
        >>> result = quick_set(data, "user.age", 30)
    """
    from .facade import XWData
    
    if not isinstance(data, XWData):
        data = XWData.from_native(data)
    
    return data.set(path, value)


def quick_delete(data: Any, path: str) -> 'XWData':
    """
    Quick delete value at path (returns new XWData with COW).
    
    Args:
        data: Data to modify
        path: Path to delete
        
    Returns:
        New XWData instance
    """
    from .facade import XWData
    
    if not isinstance(data, XWData):
        data = XWData.from_native(data)
    
    return data.delete(path)


# =============================================================================
# QUICK MERGE/DIFF/PATCH SHORTCUTS  
# =============================================================================

def quick_merge(target: Any, source: Any, strategy: str = "deep") -> 'XWData':
    """
    Quick merge two data structures.
    
    Args:
        target: Target data
        source: Source data
        strategy: Merge strategy (deep, shallow, overwrite, append, unique)
        
    Returns:
        Merged XWData
        
    Examples:
        >>> from exonware.xwdata import quick_merge
        >>> result = quick_merge(
        ...     {"a": 1, "b": {"c": 2}},
        ...     {"b": {"d": 3}}
        ... )
        >>> # Result: {"a": 1, "b": {"c": 2, "d": 3}}
    """
    from .operations import merge_data, MergeStrategy
    
    strategy_map = {
        "deep": MergeStrategy.DEEP,
        "shallow": MergeStrategy.SHALLOW,
        "overwrite": MergeStrategy.OVERWRITE,
        "append": MergeStrategy.APPEND,
        "unique": MergeStrategy.UNIQUE
    }
    
    merge_strategy = strategy_map.get(strategy, MergeStrategy.DEEP)
    return merge_data(target, source, strategy=merge_strategy)


def quick_diff(original: Any, modified: Any) -> dict[str, Any]:
    """
    Quick diff between two data structures.
    
    Args:
        original: Original data
        modified: Modified data
        
    Returns:
        dict with diff results
        
    Examples:
        >>> from exonware.xwdata import quick_diff
        >>> result = quick_diff(
        ...     {"a": 1, "b": 2},
        ...     {"a": 1, "b": 3}
        ... )
        >>> print(result["total_changes"])  # 1
    """
    from .operations import diff_data, DiffMode
    
    result = diff_data(original, modified, mode=DiffMode.FULL)
    
    return {
        "operations": result.operations,
        "paths_changed": result.paths_changed,
        "total_changes": result.total_changes,
        "mode": result.mode.value
    }


def quick_patch(data: Any, operations: list[dict[str, Any]]) -> Any:
    """
    Quick apply patch operations.
    
    Args:
        data: Data to patch
        operations: RFC 6902 patch operations
        
    Returns:
        Patched data
        
    Examples:
        >>> from exonware.xwdata import quick_patch
        >>> result = quick_patch(
        ...     {"a": 1},
        ...     [{"op": "add", "path": "/b", "value": 2}]
        ... )
        >>> # Result: {"a": 1, "b": 2}
    """
    from .operations import patch_data
    
    result = patch_data(data, operations)
    return result.result if result.success else data


# =============================================================================
# QUICK VALIDATION SHORTCUTS
# =============================================================================

def quick_validate(data: Any, schema: dict[str, Any]) -> bool:
    """
    Quick validate data against schema.
    
    Uses xwschema if available for comprehensive schema validation.
    Falls back to basic validation if xwschema is not available.
    
    Args:
        data: Data to validate (XWData or native)
        schema: Validation schema (JSON Schema, OpenAPI, etc.)
        
    Returns:
        True if valid, False otherwise
        
    Examples:
        >>> from exonware.xwdata import quick_validate
        >>> schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        >>> quick_validate({"name": "Alice"}, schema)  # True
        >>> quick_validate({"name": 123}, schema)  # False
        
    Priority Alignment:
    - Security: Validates data against schema for security
    - Usability: Simple, one-liner validation
    - Maintainability: Delegates to xwschema when available
    """
    from .facade import XWData
    
    # Convert to XWData if needed
    if not isinstance(data, XWData):
        data = XWData.from_native(data)
    
    # Try to use xwschema for comprehensive validation (optional dependency)
    # Note: xwschema depends on xwdata, so we must handle this carefully to avoid circular imports
    # We use a late import pattern with try/except to make this optional
    try:
        # Late import - only imported when validation is actually called
        # This prevents circular dependency issues at module load time
        from exonware.xwschema import XWSchema
        
        # Create schema instance from dict (XWSchema accepts dict in constructor)
        schema_obj = XWSchema(schema)
        
        # Validate data - XWSchema.validate returns tuple (is_valid, errors)
        try:
            # XWSchema.validate is async, but we need sync for shortcuts
            # Use asyncio if available, otherwise run in new event loop
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Event loop already running - use sync wrapper
                    is_valid, errors = _sync_validate(schema_obj, data.to_native())
                else:
                    # No running loop - can use asyncio.run
                    is_valid, errors = asyncio.run(schema_obj.validate(data.to_native()))
            except RuntimeError:
                # No event loop - create one
                is_valid, errors = asyncio.run(schema_obj.validate(data.to_native()))
        except Exception as e:
            # Fallback if async validation fails
            from exonware.xwsystem import get_logger
            logger = get_logger(__name__)
            logger.debug(f"Async validation failed, using basic validation: {e}")
            is_valid = _basic_validate(data.to_native(), schema)
        
        return is_valid
    except Exception:
        # Fallback to basic validation if xwschema not available
        return _basic_validate(data.to_native(), schema)


def _sync_validate(schema_obj: Any, data: Any) -> tuple[bool, list[str]]:
    """
    Synchronous wrapper for async validation.
    
    Args:
        schema_obj: XWSchema instance
        data: Data to validate
        
    Returns:
        Tuple of (is_valid, errors)
    """
    import asyncio
    new_loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(new_loop)
        return new_loop.run_until_complete(schema_obj.validate(data))
    finally:
        new_loop.close()
        asyncio.set_event_loop(None)


def _basic_validate(data: Any, schema: dict[str, Any]) -> bool:
    """
    Basic validation when xwschema is not available.
    
    Performs simple structural validation:
    - Type checking (string, number, object, array, boolean, null)
    - Required fields checking
    - Basic structure validation
    
    Args:
        data: Data to validate
        schema: JSON Schema-like structure
        
    Returns:
        True if valid, False otherwise
    """
    # Basic type validation
    if 'type' in schema:
        expected_type = schema['type']
        actual_type = _get_type_name(data)
        
        if expected_type == 'object' and not isinstance(data, dict):
            return False
        elif expected_type == 'array' and not isinstance(data, list):
            return False
        elif expected_type == 'string' and not isinstance(data, str):
            return False
        elif expected_type == 'number' and not isinstance(data, (int, float)):
            return False
        elif expected_type == 'integer' and not isinstance(data, int):
            return False
        elif expected_type == 'boolean' and not isinstance(data, bool):
            return False
        elif expected_type == 'null' and data is not None:
            return False
    
    # Check required fields for objects
    if isinstance(data, dict) and 'required' in schema:
        required = schema['required']
        for field in required:
            if field not in data:
                return False
    
    # Validate properties for objects
    if isinstance(data, dict) and 'properties' in schema:
        properties = schema['properties']
        for key, value in data.items():
            if key in properties:
                # Recursively validate property
                if not _basic_validate(value, properties[key]):
                    return False
    
    # Validate items for arrays
    if isinstance(data, list) and 'items' in schema:
        items_schema = schema['items']
        for item in data:
            if not _basic_validate(item, items_schema):
                return False
    
    return True


def _get_type_name(value: Any) -> str:
    """Get JSON Schema type name for Python value."""
    if value is None:
        return 'null'
    elif isinstance(value, bool):
        return 'boolean'
    elif isinstance(value, int):
        return 'integer'
    elif isinstance(value, (int, float)):
        return 'number'
    elif isinstance(value, str):
        return 'string'
    elif isinstance(value, list):
        return 'array'
    elif isinstance(value, dict):
        return 'object'
    else:
        return 'unknown'


__all__ = [
    # Load/Save
    "quick_load",
    "quick_save",
    "quick_convert",
    # Format conversion
    "to_json",
    "to_yaml",
    "to_xml",
    "to_toml",
    "to_csv",
    "from_json",
    "from_yaml",
    "from_xml",
    "from_toml",
    "from_csv",
    # Query
    "quick_get",
    "quick_set",
    "quick_delete",
    # Operations
    "quick_merge",
    "quick_diff",
    "quick_patch",
    # Validation
    "quick_validate",
]

