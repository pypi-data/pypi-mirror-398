#!/usr/bin/env python3
"""
#exonware/xwdata/src/exonware/xwdata/operations/data_patch.py

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: October 27, 2025

Data-aware patch operations using xwsystem.operations.
"""

from typing import Any
from exonware.xwsystem.operations import apply_patch, PatchResult


class DataPatcher:
    """
    Data-aware patcher with XWData support.
    
    Priority Alignment:
    1. Security - Safe patching  
    2. Usability - Simple patch API
    3. Maintainability - Delegates to xwsystem
    4. Performance - Efficient patching
    5. Extensibility - RFC 6902 compliant
    """
    
    def patch(
        self,
        data: Any,
        operations: list[dict[str, Any]],
        preserve_types: bool = True
    ) -> PatchResult:
        """
        Apply patch operations to data.
        
        Args:
            data: Data to patch
            operations: RFC 6902 patch operations
            preserve_types: Preserve XWData types
            
        Returns:
            PatchResult with patched data
        """
        from ..facade import XWData
        
        native_data = data.to_native() if isinstance(data, XWData) else data
        
        result = apply_patch(native_data, operations)
        
        # Preserve XWData type if requested
        if isinstance(data, XWData) and preserve_types and result.success:
            result.result = XWData.from_native(result.result)
        
        return result


def patch_data(
    data: Any,
    operations: list[dict[str, Any]]
) -> PatchResult:
    """
    Convenience function for patching data.
    
    Examples:
        >>> from exonware.xwdata import patch_data
        >>> result = patch_data(
        ...     {"a": 1, "b": 2},
        ...     [{"op": "replace", "path": "/b", "value": 3}]
        ... )
        >>> print(result.result)  # {"a": 1, "b": 3}
    """
    patcher = DataPatcher()
    return patcher.patch(data, operations)


__all__ = ["DataPatcher", "patch_data"]

