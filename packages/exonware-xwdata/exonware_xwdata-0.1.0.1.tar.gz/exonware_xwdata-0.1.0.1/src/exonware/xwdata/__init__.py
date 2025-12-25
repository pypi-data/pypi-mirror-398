#!/usr/bin/env python3
"""
#exonware/xwdata/src/exonware/xwdata/__init__.py

xwdata: Advanced Data Manipulation with XWNode Integration

The xwdata library provides universal data manipulation with:
- Format-agnostic operations (load from any format, save to any)
- XWNode integration for powerful navigation and queries
- Copy-on-write semantics for safe concurrent access
- Universal metadata for perfect roundtrips
- Reference resolution with circular detection
- Performance caching and optimization
- Async operations by design
- Engine-driven orchestration

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 26-Oct-2025

Main Classes:
    XWData: Primary facade for data operations
    XWDataEngine: Core orchestration engine
    XWDataNode: Data node with COW semantics
    XWDataConfig: Configuration system

Example:
    >>> from exonware.xwdata import XWData
    >>> 
    >>> # Load from any format
    >>> data = await XWData.load('config.json')
    >>> 
    >>> # Navigate and modify (COW)
    >>> data = await data.set('api.timeout', 30)
    >>> 
    >>> # Save to different format
    >>> await data.save('config.yaml')  # JSON → YAML!
    >>> 
    >>> # Or synchronously from native data
    >>> data = XWData({'name': 'Alice', 'age': 30})
    >>> name = await data.get('name')  # 'Alice'
"""

# =============================================================================
# CORE IMPORTS
# =============================================================================

# Facade and main classes
from .facade import XWData, load, from_native, parse

# Builder pattern
from .builder import XWDataBuilder

# Shortcuts API
from .shortcuts import (
    quick_load, quick_save, quick_convert,
    to_json, to_yaml, to_xml, to_toml, to_csv,
    from_json, from_yaml, from_xml, from_toml, from_csv,
    quick_get, quick_set, quick_delete,
    quick_merge, quick_diff, quick_patch, quick_validate
)

# Operations (xwsystem integration)
from .operations import (
    MergeStrategy, DiffMode, PatchOperation, DiffResult, PatchResult,
    DataMerger, DataDiffer, DataPatcher, BatchOperations,
    merge_data, diff_data, patch_data,
    batch_convert, batch_validate, batch_transform
)

# Configuration
from .config import (
    XWDataConfig,
    SecurityConfig,
    PerformanceConfig,
    ReferenceConfig,
    MetadataConfig,
    COWConfig
)

# Enums and definitions
from .defs import (
    DataFormat,
    EngineMode,
    CacheStrategy,
    ReferenceResolutionMode,
    MergeStrategy,
    SerializationMode,
    COWMode,
    MetadataMode,
    ValidationMode,
    PerformanceTrait,
    SecurityTrait
)

# Errors
from .errors import (
    XWDataError,
    XWDataSecurityError,
    XWDataParseError,
    XWDataSerializeError,
    XWDataIOError,
    XWDataEngineError,
    XWDataMetadataError,
    XWDataReferenceError,
    XWDataCircularReferenceError,
    XWDataCacheError,
    XWDataNodeError,
    XWDataPathError,
    XWDataTypeError,
    XWDataValidationError,
    XWDataConfigError
)

# Engine and components (for advanced usage)
from .data.engine import XWDataEngine
from .data.node import XWDataNode
from .data.factory import NodeFactory

# Strategies (for extensibility)
from .data.strategies.registry import FormatStrategyRegistry

# Version info
from .version import (
    __version__,
    __author__,
    __email__,
    __company__,
    __description__,
    get_version,
    get_version_info
)

# =============================================================================
# PUBLIC API
# =============================================================================

__all__ = [
    # Main classes
    'XWData',
    'XWDataBuilder',
    
    # Convenience functions
    'load',
    'from_native',
    'parse',
    
    # Shortcuts API
    'quick_load', 'quick_save', 'quick_convert',
    'to_json', 'to_yaml', 'to_xml', 'to_toml', 'to_csv',
    'from_json', 'from_yaml', 'from_xml', 'from_toml', 'from_csv',
    'quick_get', 'quick_set', 'quick_delete',
    'quick_merge', 'quick_diff', 'quick_patch', 'quick_validate',
    
    # Operations (xwsystem integration)
    'MergeStrategy', 'DiffMode', 'PatchOperation', 'DiffResult', 'PatchResult',
    'DataMerger', 'DataDiffer', 'DataPatcher', 'BatchOperations',
    'merge_data', 'diff_data', 'patch_data',
    'batch_convert', 'batch_validate', 'batch_transform',
    
    # Configuration
    'XWDataConfig',
    'SecurityConfig',
    'PerformanceConfig',
    'ReferenceConfig',
    'MetadataConfig',
    'COWConfig',
    
    # Enums
    'DataFormat',
    'EngineMode',
    'CacheStrategy',
    'ReferenceResolutionMode',
    'MergeStrategy',
    'SerializationMode',
    'COWMode',
    'MetadataMode',
    'ValidationMode',
    'PerformanceTrait',
    'SecurityTrait',
    
    # Errors
    'XWDataError',
    'XWDataSecurityError',
    'XWDataParseError',
    'XWDataSerializeError',
    'XWDataIOError',
    'XWDataEngineError',
    'XWDataMetadataError',
    'XWDataReferenceError',
    'XWDataCircularReferenceError',
    'XWDataCacheError',
    'XWDataNodeError',
    'XWDataPathError',
    'XWDataTypeError',
    'XWDataValidationError',
    'XWDataConfigError',
    
    # Advanced (for extensions)
    'XWDataEngine',
    'XWDataNode',
    'NodeFactory',
    'FormatStrategyRegistry',
    
    # Version
    '__version__',
    '__author__',
    '__email__',
    '__company__',
    '__description__',
    'get_version',
    'get_version_info',
]


# =============================================================================
# LIBRARY INFORMATION
# =============================================================================

def get_info() -> dict:
    """
    Get comprehensive library information.
    
    Returns:
        Dictionary with library details
    """
    return {
        'version': __version__,
        'description': __description__,
        'author': __author__,
        'company': __company__,
        'email': __email__
    }


__all__.append('get_info')

