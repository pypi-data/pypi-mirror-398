#!/usr/bin/env python3
"""
#exonware/xwdata/src/exonware/xwdata/data/references/detector.py

Reference Detector Implementation

Detects references in data using format strategies.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 26-Oct-2025
"""

from typing import Any
from exonware.xwsystem import get_logger

from ...base import AReferenceDetector
from ...contracts import IFormatStrategy

logger = get_logger(__name__)


class ReferenceDetector(AReferenceDetector):
    """
    Reference detector using format strategies.
    
    Delegates to format strategies for format-specific
    reference pattern detection.
    """
    
    def __init__(self):
        """Initialize reference detector."""
        super().__init__()
    
    async def detect(
        self,
        data: Any,
        strategy: IFormatStrategy,
        **opts
    ) -> list[dict[str, Any]]:
        """
        Detect references in data using strategy.
        
        Args:
            data: Data to scan for references
            strategy: Format strategy
            **opts: Additional options
            
        Returns:
            List of detected references
        """
        if strategy is None:
            logger.debug("No strategy provided, skipping reference detection")
            return []
        
        # Delegate to strategy
        references = await strategy.detect_references(data, **opts)
        
        logger.debug(f"Detected {len(references)} references using {strategy.name} strategy")
        return references


__all__ = ['ReferenceDetector']

