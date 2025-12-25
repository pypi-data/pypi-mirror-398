#!/usr/bin/env python3
"""
#exonware/xwdata/src/exonware/xwdata/operations/data_diff.py

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: October 27, 2025

Data-aware diff operations using xwsystem.operations.
"""

from typing import Any
from exonware.xwsystem.operations import generate_diff, DiffMode, DiffResult


class DataDiffer:
    """
    Data-aware differ with XWData support.
    
    Priority Alignment:
    1. Security - Safe comparison
    2. Usability - Simple diff API  
    3. Maintainability - Delegates to xwsystem
    4. Performance - Efficient comparison
    5. Extensibility - Multiple diff modes
    """
    
    def diff(
        self,
        original: Any,
        modified: Any,
        mode: DiffMode = DiffMode.FULL
    ) -> DiffResult:
        """
        Generate diff between two data structures.
        
        Args:
            original: Original data
            modified: Modified data
            mode: Diff mode
            
        Returns:
            DiffResult with operations
        """
        from ..facade import XWData
        
        orig_native = original.to_native() if isinstance(original, XWData) else original
        mod_native = modified.to_native() if isinstance(modified, XWData) else modified
        
        return generate_diff(orig_native, mod_native, mode=mode)


def diff_data(
    original: Any,
    modified: Any,
    mode: DiffMode = DiffMode.FULL
) -> DiffResult:
    """
    Convenience function for diffing data.
    
    Examples:
        >>> from exonware.xwdata import diff_data, DiffMode
        >>> result = diff_data(
        ...     {"a": 1, "b": 2},
        ...     {"a": 1, "b": 3},
        ...     mode=DiffMode.FULL
        ... )
        >>> print(result.total_changes)  # 1
    """
    differ = DataDiffer()
    return differ.diff(original, modified, mode=mode)


__all__ = ["DataDiffer", "diff_data"]

