#!/usr/bin/env python3
"""
#exonware/xwdata/src/exonware/xwdata/common/benchmarking.py

Performance Benchmarking Utilities for XWData

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 15-Nov-2025
"""

import time
import statistics
from typing import Any, Callable, Optional, Dict, List
from dataclasses import dataclass
from pathlib import Path
from exonware.xwsystem import get_logger

logger = get_logger(__name__)


@dataclass
class DataOperationResult:
    """Result of a data operation benchmark."""
    operation: str
    format: str
    iterations: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    median_time: float
    std_dev: float
    throughput: float  # operations per second
    memory_usage: Optional[float] = None


class XWDataBenchmark:
    """Benchmark utilities for XWData operations."""
    
    @staticmethod
    def benchmark_load(
        file_path: Path,
        format_hint: Optional[str] = None,
        iterations: int = 100,
        warmup: int = 10
    ) -> DataOperationResult:
        """
        Benchmark file loading operation.
        
        Args:
            file_path: Path to file to load
            format_hint: Optional format hint
            iterations: Number of iterations
            warmup: Number of warmup iterations
            
        Returns:
            DataOperationResult with statistics
        """
        from ..facade import XWData
        
        # Warmup
        for _ in range(warmup):
            try:
                import asyncio
                asyncio.run(XWData.load(file_path, format_hint=format_hint))
            except Exception:
                pass
        
        # Actual benchmark
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            try:
                import asyncio
                asyncio.run(XWData.load(file_path, format_hint=format_hint))
            except Exception as e:
                logger.warning(f"Load operation failed: {e}")
            end = time.perf_counter()
            times.append(end - start)
        
        total_time = sum(times)
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        median_time = statistics.median(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0.0
        throughput = iterations / total_time if total_time > 0 else 0.0
        
        return DataOperationResult(
            operation="load",
            format=format_hint or file_path.suffix.lstrip('.'),
            iterations=iterations,
            total_time=total_time,
            avg_time=avg_time,
            min_time=min_time,
            max_time=max_time,
            median_time=median_time,
            std_dev=std_dev,
            throughput=throughput
        )
    
    @staticmethod
    def benchmark_save(
        data: Any,
        file_path: Path,
        format_hint: Optional[str] = None,
        iterations: int = 100,
        warmup: int = 10
    ) -> DataOperationResult:
        """
        Benchmark file saving operation.
        
        Args:
            data: Data to save
            file_path: Path to save to
            format_hint: Optional format hint
            iterations: Number of iterations
            warmup: Number of warmup iterations
            
        Returns:
            DataOperationResult with statistics
        """
        from ..facade import XWData
        
        # Warmup
        for _ in range(warmup):
            try:
                import asyncio
                xwdata = XWData(data)
                asyncio.run(xwdata.save(file_path, format_hint=format_hint))
            except Exception:
                pass
        
        # Actual benchmark
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            try:
                import asyncio
                xwdata = XWData(data)
                asyncio.run(xwdata.save(file_path, format_hint=format_hint))
            except Exception as e:
                logger.warning(f"Save operation failed: {e}")
            end = time.perf_counter()
            times.append(end - start)
        
        total_time = sum(times)
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        median_time = statistics.median(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0.0
        throughput = iterations / total_time if total_time > 0 else 0.0
        
        return DataOperationResult(
            operation="save",
            format=format_hint or file_path.suffix.lstrip('.'),
            iterations=iterations,
            total_time=total_time,
            avg_time=avg_time,
            min_time=min_time,
            max_time=max_time,
            median_time=median_time,
            std_dev=std_dev,
            throughput=throughput
        )
    
    @staticmethod
    def benchmark_conversion(
        source_path: Path,
        target_format: str,
        iterations: int = 50,
        warmup: int = 5
    ) -> DataOperationResult:
        """
        Benchmark format conversion operation.
        
        Args:
            source_path: Source file path
            target_format: Target format
            iterations: Number of iterations
            warmup: Number of warmup iterations
            
        Returns:
            DataOperationResult with statistics
        """
        from ..facade import XWData
        
        # Warmup
        for _ in range(warmup):
            try:
                import asyncio
                data = asyncio.run(XWData.load(source_path))
                target_path = source_path.with_suffix(f'.{target_format}')
                asyncio.run(data.save(target_path))
            except Exception:
                pass
        
        # Actual benchmark
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            try:
                import asyncio
                data = asyncio.run(XWData.load(source_path))
                target_path = source_path.with_suffix(f'.{target_format}')
                asyncio.run(data.save(target_path))
            except Exception as e:
                logger.warning(f"Conversion operation failed: {e}")
            end = time.perf_counter()
            times.append(end - start)
        
        total_time = sum(times)
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        median_time = statistics.median(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0.0
        throughput = iterations / total_time if total_time > 0 else 0.0
        
        return DataOperationResult(
            operation="conversion",
            format=target_format,
            iterations=iterations,
            total_time=total_time,
            avg_time=avg_time,
            min_time=min_time,
            max_time=max_time,
            median_time=median_time,
            std_dev=std_dev,
            throughput=throughput
        )

