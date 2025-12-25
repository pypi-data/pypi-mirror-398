#!/usr/bin/env python3
"""
#exonware/xwdata/src/exonware/xwdata/config.py

XWData Configuration System

This module provides fluent configuration for xwdata with builder pattern
and sensible defaults for different use cases.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 26-Oct-2025
"""

from dataclasses import dataclass, field
from typing import Optional, Any
from pathlib import Path

from enum import Enum
from .defs import (
    CacheStrategy, ReferenceResolutionMode, MergeStrategy,
    COWMode, MetadataMode, ValidationMode,
    DEFAULT_CACHE_SIZE, DEFAULT_MAX_FILE_SIZE_MB,
    DEFAULT_MAX_NESTING_DEPTH, DEFAULT_TIMEOUT_SECONDS,
    DEFAULT_MERGE_STRATEGY
)


# ==============================================================================
# V8 ENUMS
# ==============================================================================

class LoadStrategy(Enum):
    """Loading strategy based on file size (V8)."""
    FULL = "full"              # Load entire file into memory
    LAZY = "lazy"              # Defer loading until accessed
    PARTIAL = "partial"        # Use partial access (JSON Pointer/ijson)
    STREAMING = "streaming"    # Stream-only (no full load)
    AUTO = "auto"              # Automatic detection (default)


# ==============================================================================
# SECURITY CONFIGURATION
# ==============================================================================

@dataclass
class SecurityConfig:
    """Security configuration with defensive defaults."""
    
    max_file_size_mb: int = DEFAULT_MAX_FILE_SIZE_MB
    max_nesting_depth: int = DEFAULT_MAX_NESTING_DEPTH
    safe_mode: bool = True
    allowed_schemes: tuple[str, ...] = ('file', 'https')
    deny_extensions: tuple[str, ...] = ('exe', 'bat', 'sh', 'cmd', 'scr')
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    enable_path_validation: bool = True
    enable_sanitization: bool = True
    
    @classmethod
    def strict(cls) -> 'SecurityConfig':
        """High security mode for untrusted data."""
        return cls(
            max_file_size_mb=10,
            max_nesting_depth=20,
            safe_mode=True,
            allowed_schemes=('file',),
            deny_extensions=('exe', 'bat', 'sh', 'py', 'scr', 'cmd', 'vbs'),
            timeout_seconds=10,
            enable_path_validation=True,
            enable_sanitization=True
        )
    
    @classmethod
    def relaxed(cls) -> 'SecurityConfig':
        """Development mode with relaxed limits."""
        return cls(
            max_file_size_mb=500,
            max_nesting_depth=100,
            safe_mode=False,
            allowed_schemes=('file', 'http', 'https', 'ftp'),
            deny_extensions=(),
            timeout_seconds=300,
            enable_path_validation=False,
            enable_sanitization=False
        )


# ==============================================================================
# PERFORMANCE CONFIGURATION
# ==============================================================================

@dataclass
class PerformanceConfig:
    """Performance configuration for optimization."""
    
    cache_strategy: CacheStrategy = CacheStrategy.TWO_TIER
    cache_size: int = DEFAULT_CACHE_SIZE
    enable_caching: bool = True
    enable_streaming: bool = True
    enable_disk_cache: bool = False
    disk_cache_dir: Optional[Path] = None
    enable_pooling: bool = True
    enable_structural_hashing: bool = True
    pool_size: int = 100
    enable_parallel: bool = False
    max_workers: int = 4
    
    # Fast path optimizations (inspired by xData-Old's simplicity)
    enable_fast_path: bool = True  # Use fast path for small operations
    fast_path_threshold_kb: int = 50  # Files < 50KB use fast path (increased from 10KB)
    enable_direct_navigation: bool = True  # Bypass XWNode for simple paths
    direct_nav_size_threshold_kb: int = 100  # Use direct nav when data > 100KB
    
    @classmethod
    def fast(cls) -> 'PerformanceConfig':
        """High performance mode with fast path enabled."""
        return cls(
            cache_strategy=CacheStrategy.TWO_TIER,
            cache_size=5000,
            enable_caching=True,
            enable_streaming=True,
            enable_disk_cache=True,
            enable_pooling=True,
            enable_structural_hashing=True,
            pool_size=500,
            enable_parallel=True,
            max_workers=8,
            enable_fast_path=True,  # xData-Old style for small files
            fast_path_threshold_kb=10,
            enable_direct_navigation=True,  # Direct dict access
            direct_nav_size_threshold_kb=100
        )
    
    @classmethod
    def memory_optimized(cls) -> 'PerformanceConfig':
        """Memory-efficient mode."""
        return cls(
            cache_strategy=CacheStrategy.NONE,
            cache_size=100,
            enable_caching=False,
            enable_streaming=True,
            enable_disk_cache=False,
            enable_pooling=False,
            enable_structural_hashing=False,
            pool_size=10,
            enable_parallel=False
        )


# ==============================================================================
# LAZY CONFIGURATION (Industry Best Practices)
# ==============================================================================

@dataclass
class LazyConfig:
    """
    Lazy loading configuration following industry best practices.
    
    Industry Standards:
    - Virtual Proxy Pattern: Defer expensive operations until needed
    - Lazy Initialization: Initialize objects only when accessed
    - Lazy Evaluation: Defer computation until results are required
    - Memory Efficiency: Reduce memory footprint for large datasets
    - Performance Optimization: Avoid unnecessary work
    """
    
    # Core lazy capabilities
    defer_file_io: bool = True  # Don't read file until accessed
    defer_serialization: bool = True  # Don't parse until accessed
    defer_xwnode_creation: bool = True  # Don't create XWNode until needed
    defer_metadata_extraction: bool = False  # Always extract metadata (security)
    
    # Thresholds for lazy behavior
    file_size_threshold_kb: int = 10  # Files < 10KB never lazy (fast path)
    data_size_threshold_kb: int = 100  # Data < 100KB never lazy
    navigation_depth_threshold: int = 3  # Deep paths trigger lazy
    
    # Lazy evaluation strategies
    enable_lazy_evaluation: bool = True  # Defer computation
    enable_lazy_validation: bool = True  # Defer validation until access
    enable_lazy_caching: bool = True  # Cache lazy results
    
    # Memory management
    enable_memory_mapping: bool = False  # Use memory mapping for large files
    enable_streaming_parsing: bool = True  # Stream parse large files
    enable_chunked_loading: bool = True  # Load data in chunks
    
    # Performance optimizations
    enable_prefetching: bool = False  # Prefetch likely-to-be-accessed data
    prefetch_distance: int = 2  # How many levels to prefetch
    enable_smart_caching: bool = True  # Cache based on access patterns
    
    @classmethod
    def aggressive(cls) -> 'LazyConfig':
        """Maximum lazy loading for memory efficiency."""
        return cls(
            defer_file_io=True,
            defer_serialization=True,
            defer_xwnode_creation=True,
            defer_metadata_extraction=True,  # Even metadata is lazy
            file_size_threshold_kb=5,  # Smaller threshold
            data_size_threshold_kb=50,
            navigation_depth_threshold=2,
            enable_lazy_evaluation=True,
            enable_lazy_validation=True,
            enable_lazy_caching=True,
            enable_memory_mapping=True,
            enable_streaming_parsing=True,
            enable_chunked_loading=True,
            enable_prefetching=False,  # Aggressive = no prefetch
            enable_smart_caching=True
        )
    
    @classmethod
    def smart(cls) -> 'LazyConfig':
        """Balanced lazy loading with smart optimizations."""
        return cls(
            defer_file_io=True,
            defer_serialization=True,
            defer_xwnode_creation=True,
            defer_metadata_extraction=False,  # Always extract metadata
            file_size_threshold_kb=10,
            data_size_threshold_kb=100,
            navigation_depth_threshold=3,
            enable_lazy_evaluation=True,
            enable_lazy_validation=True,
            enable_lazy_caching=True,
            enable_memory_mapping=False,
            enable_streaming_parsing=True,
            enable_chunked_loading=True,
            enable_prefetching=True,  # Smart prefetching
            prefetch_distance=2,
            enable_smart_caching=True
        )
    
    @classmethod
    def minimal(cls) -> 'LazyConfig':
        """Minimal lazy loading for performance."""
        return cls(
            defer_file_io=False,  # Always read immediately
            defer_serialization=False,  # Always parse immediately
            defer_xwnode_creation=False,  # Always create XWNode
            defer_metadata_extraction=False,
            file_size_threshold_kb=50,  # Higher threshold
            data_size_threshold_kb=500,
            navigation_depth_threshold=5,
            enable_lazy_evaluation=False,
            enable_lazy_validation=False,
            enable_lazy_caching=False,
            enable_memory_mapping=False,
            enable_streaming_parsing=False,
            enable_chunked_loading=False,
            enable_prefetching=False,
            enable_smart_caching=False
        )
    
    @classmethod
    def off(cls) -> 'LazyConfig':
        """Disable all lazy loading."""
        return cls(
            defer_file_io=False,
            defer_serialization=False,
            defer_xwnode_creation=False,
            defer_metadata_extraction=False,
            file_size_threshold_kb=0,  # No threshold
            data_size_threshold_kb=0,
            navigation_depth_threshold=0,
            enable_lazy_evaluation=False,
            enable_lazy_validation=False,
            enable_lazy_caching=False,
            enable_memory_mapping=False,
            enable_streaming_parsing=False,
            enable_chunked_loading=False,
            enable_prefetching=False,
            enable_smart_caching=False
        )


# ==============================================================================
# REFERENCE CONFIGURATION (Industry Best Practices)
# ==============================================================================

@dataclass
class ReferenceConfig:
    """
    Reference resolution configuration following industry best practices.
    
    Industry Standards:
    - JSON Schema $ref: RFC 3986 URI resolution
    - OpenAPI $ref: JSON Reference specification
    - XML XInclude: W3C XInclude specification
    - YAML Anchors: YAML 1.2 specification
    - Security: Path traversal prevention, scheme validation
    - Performance: Caching, lazy resolution, circular detection
    """
    
    # Core resolution behavior
    resolution_mode: ReferenceResolutionMode = ReferenceResolutionMode.LAZY
    enable_circular_detection: bool = True
    max_resolution_depth: int = 10
    cache_resolved: bool = True
    follow_external: bool = True
    allowed_schemes: tuple[str, ...] = ('file', 'https')
    
    # Format-specific patterns (industry standard)
    json_ref_patterns: tuple[str, ...] = ('$ref', '$id', '$anchor')
    xml_ref_patterns: tuple[str, ...] = ('@href', '@xlink:href', 'xi:include')
    yaml_ref_patterns: tuple[str, ...] = ('*', '&', '<<')
    custom_ref_patterns: tuple[str, ...] = ()  # User-defined patterns
    
    # Security controls
    enable_path_validation: bool = True  # Prevent ../ attacks
    enable_scheme_validation: bool = True  # Only allow safe schemes
    enable_content_validation: bool = True  # Validate resolved content
    max_external_size_mb: int = 10  # Limit external reference size
    timeout_seconds: int = 30  # Timeout for external references
    
    # Performance optimizations
    enable_reference_caching: bool = True  # Cache resolved references
    enable_lazy_resolution: bool = True  # Resolve only when accessed
    enable_batch_resolution: bool = True  # Resolve multiple refs together
    enable_prefetching: bool = False  # Prefetch likely references
    
    # Error handling
    fail_on_missing_ref: bool = True  # Fail if reference not found
    fail_on_circular_ref: bool = True  # Fail on circular references
    fail_on_invalid_ref: bool = True  # Fail on invalid reference format
    
    @classmethod
    def eager(cls) -> 'ReferenceConfig':
        """Eager resolution mode - resolve all references immediately."""
        return cls(
            resolution_mode=ReferenceResolutionMode.EAGER,
            enable_circular_detection=True,
            max_resolution_depth=20,
            cache_resolved=True,
            follow_external=True,
            enable_lazy_resolution=False,  # Resolve immediately
            enable_batch_resolution=True,
            enable_prefetching=True,
            fail_on_missing_ref=True,
            fail_on_circular_ref=True,
            fail_on_invalid_ref=True
        )
    
    @classmethod
    def lazy(cls) -> 'ReferenceConfig':
        """Lazy resolution mode - resolve references when accessed."""
        return cls(
            resolution_mode=ReferenceResolutionMode.LAZY,
            enable_circular_detection=True,
            max_resolution_depth=10,
            cache_resolved=True,
            follow_external=True,
            enable_lazy_resolution=True,  # Resolve on access
            enable_batch_resolution=False,
            enable_prefetching=False,
            fail_on_missing_ref=False,  # Don't fail until accessed
            fail_on_circular_ref=True,
            fail_on_invalid_ref=False
        )
    
    @classmethod
    def detect_only(cls) -> 'ReferenceConfig':
        """Detect references but don't resolve."""
        return cls(
            resolution_mode=ReferenceResolutionMode.DETECT_ONLY,
            enable_circular_detection=False,
            max_resolution_depth=0,
            cache_resolved=False,
            follow_external=False,
            enable_lazy_resolution=False,
            enable_batch_resolution=False,
            enable_prefetching=False,
            fail_on_missing_ref=False,
            fail_on_circular_ref=False,
            fail_on_invalid_ref=False
        )
    
    @classmethod
    def secure(cls) -> 'ReferenceConfig':
        """High security mode for untrusted data."""
        return cls(
            resolution_mode=ReferenceResolutionMode.LAZY,
            enable_circular_detection=True,
            max_resolution_depth=5,  # Shallow depth
            cache_resolved=False,  # No caching for security
            follow_external=False,  # No external references
            allowed_schemes=('file',),  # Only local files
            enable_path_validation=True,
            enable_scheme_validation=True,
            enable_content_validation=True,
            max_external_size_mb=1,  # Very small limit
            timeout_seconds=5,  # Short timeout
            fail_on_missing_ref=True,
            fail_on_circular_ref=True,
            fail_on_invalid_ref=True
        )
    
    @classmethod
    def off(cls) -> 'ReferenceConfig':
        """Disable all reference resolution."""
        return cls(
            resolution_mode=ReferenceResolutionMode.DETECT_ONLY,
            enable_circular_detection=False,
            max_resolution_depth=0,
            cache_resolved=False,
            follow_external=False,
            enable_lazy_resolution=False,
            enable_batch_resolution=False,
            enable_prefetching=False,
            fail_on_missing_ref=False,
            fail_on_circular_ref=False,
            fail_on_invalid_ref=False
        )


# ==============================================================================
# METADATA CONFIGURATION
# ==============================================================================

@dataclass
class MetadataConfig:
    """Metadata preservation configuration."""
    
    mode: MetadataMode = MetadataMode.UNIVERSAL
    preserve_format_specifics: bool = True
    preserve_types: bool = True
    preserve_order: bool = True
    preserve_comments: bool = False  # Not all formats support
    enable_universal_metadata: bool = True
    
    @classmethod
    def minimal(cls) -> 'MetadataConfig':
        """Minimal metadata mode."""
        return cls(
            mode=MetadataMode.BASIC,
            preserve_format_specifics=False,
            preserve_types=True,
            preserve_order=False,
            preserve_comments=False,
            enable_universal_metadata=False
        )
    
    @classmethod
    def full(cls) -> 'MetadataConfig':
        """Full metadata preservation mode."""
        return cls(
            mode=MetadataMode.UNIVERSAL,
            preserve_format_specifics=True,
            preserve_types=True,
            preserve_order=True,
            preserve_comments=True,
            enable_universal_metadata=True
        )


# ==============================================================================
# COW CONFIGURATION
# ==============================================================================

@dataclass
class COWConfig:
    """Copy-on-write configuration."""
    
    mode: COWMode = COWMode.ENABLED
    copy_on_init: bool = False
    structural_sharing: bool = True
    freeze_on_copy: bool = True
    
    @classmethod
    def immutable(cls) -> 'COWConfig':
        """Fully immutable mode."""
        return cls(
            mode=COWMode.DEEP_COPY,
            copy_on_init=True,
            structural_sharing=False,
            freeze_on_copy=True
        )
    
    @classmethod
    def mutable(cls) -> 'COWConfig':
        """Mutable mode (no COW)."""
        return cls(
            mode=COWMode.DISABLED,
            copy_on_init=False,
            structural_sharing=False,
            freeze_on_copy=False
        )


# ==============================================================================
# V8 CONFIGURATION
# ==============================================================================

@dataclass
class SizeThresholds:
    """
    File size thresholds for automatic strategy selection (V8).
    
    Based on production best practices:
    - Small: Full load (instant, all in memory)
    - Medium: Lazy load (defer until accessed)
    - Large: Partial access (ijson, JSON Pointer)
    - Ultra: Streaming only (constant memory)
    """
    
    small_mb: float = 1.0       # < 1MB: FULL load
    medium_mb: float = 50.0     # < 50MB: LAZY load
    large_mb: float = 500.0     # < 500MB: PARTIAL access
    # > 500MB: STREAMING only
    
    @classmethod
    def aggressive(cls) -> 'SizeThresholds':
        """More aggressive partial access (use for memory-constrained systems)."""
        return cls(
            small_mb=0.5,
            medium_mb=10.0,
            large_mb=100.0
        )
    
    @classmethod
    def relaxed(cls) -> 'SizeThresholds':
        """Relaxed thresholds (use for high-memory systems)."""
        return cls(
            small_mb=10.0,
            medium_mb=100.0,
            large_mb=1000.0
        )


@dataclass
class IntegrityConfig:
    """
    File integrity configuration (V8).
    
    Checksums are OFF by default for maximum performance.
    """
    
    # OFF by default (benchmarks win!)
    enable_checksums: bool = False
    checksum_algorithm: str = 'xxh3'  # 30GB/s - near-zero overhead
    verify_on_load: bool = True
    verify_on_save: bool = True
    checksum_storage: str = 'meta_file'  # or 'embedded', 'xattr'
    fail_on_mismatch: bool = True
    
    @classmethod
    def enabled(cls) -> 'IntegrityConfig':
        """Enable checksums with fast algorithm."""
        return cls(enable_checksums=True)
    
    @classmethod
    def secure(cls) -> 'IntegrityConfig':
        """Secure checksums with SHA256."""
        return cls(
            enable_checksums=True,
            checksum_algorithm='sha256'
        )


@dataclass
class PartialAccessConfig:
    """
    Partial access configuration for large files (V8).
    
    Enables smart partial read/write based on file size.
    """
    
    # Partial access features (all OFF by default for V6 performance)
    enable_partial_read: bool = False   # Use JSON Pointer/ijson
    enable_partial_write: bool = False  # Use JSON Patch
    enable_node_streaming: bool = False # Use node-based streaming
    
    # Auto-enable based on file size (smart mode)
    auto_enable_on_size: bool = True    # Auto-detect when to use partial
    partial_threshold_mb: float = 50.0  # Auto-enable if file > 50MB
    
    # Streaming configuration
    node_buffer_size: int = 100         # Buffer 100 nodes
    stream_batch_size: int = 1000       # Process 1000 nodes per batch
    
    # Performance
    enable_path_caching: bool = True    # Cache partial access results
    cache_ttl_seconds: int = 300
    
    @classmethod
    def enabled(cls) -> 'PartialAccessConfig':
        """Enable all partial access features."""
        return cls(
            enable_partial_read=True,
            enable_partial_write=True,
            enable_node_streaming=True
        )
    
    @classmethod
    def smart(cls) -> 'PartialAccessConfig':
        """Smart mode: Auto-enable based on file size (recommended)."""
        return cls(
            auto_enable_on_size=True,
            partial_threshold_mb=50.0
        )


# ==============================================================================
# MAIN CONFIGURATION
# ==============================================================================

@dataclass
class XWDataConfig:
    """
    Main xwdata configuration with fluent builder pattern.
    
    Aggregates all configuration aspects:
    - Security: File size limits, path validation
    - Performance: Caching, pooling, parallel processing
    - References: Resolution mode, circular detection
    - Metadata: Preservation mode, universal metadata
    - COW: Copy-on-write semantics
    - V8: Smart loading, partial access, checksums
    """
    
    # Component configurations (V7)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    lazy: LazyConfig = field(default_factory=LazyConfig)
    reference: ReferenceConfig = field(default_factory=ReferenceConfig)
    metadata: MetadataConfig = field(default_factory=MetadataConfig)
    cow: COWConfig = field(default_factory=COWConfig)
    
    # V8 configurations (advanced features - OFF by default for performance)
    thresholds: SizeThresholds = field(default_factory=SizeThresholds)
    integrity: IntegrityConfig = field(default_factory=IntegrityConfig)
    partial: PartialAccessConfig = field(default_factory=PartialAccessConfig)
    
    # General settings
    default_merge_strategy: str = DEFAULT_MERGE_STRATEGY
    enable_validation: bool = True
    validation_mode: ValidationMode = ValidationMode.BASIC
    async_by_default: bool = True
    
    # Presets
    @classmethod
    def default(cls) -> 'XWDataConfig':
        """Default balanced configuration."""
        return cls()
    
    @classmethod
    def strict(cls) -> 'XWDataConfig':
        """Strict mode for untrusted data."""
        return cls(
            security=SecurityConfig.strict(),
            performance=PerformanceConfig.memory_optimized(),
            reference=ReferenceConfig.detect_only(),
            metadata=MetadataConfig.minimal(),
            cow=COWConfig.immutable(),
            enable_validation=True,
            validation_mode=ValidationMode.STRICT
        )
    
    @classmethod
    def fast(cls) -> 'XWDataConfig':
        """High performance mode."""
        return cls(
            security=SecurityConfig.relaxed(),
            performance=PerformanceConfig.fast(),
            reference=ReferenceConfig.eager(),
            metadata=MetadataConfig.minimal(),
            cow=COWConfig(),
            enable_validation=False
        )
    
    @classmethod
    def development(cls) -> 'XWDataConfig':
        """Development mode with debugging features."""
        return cls(
            security=SecurityConfig.relaxed(),
            performance=PerformanceConfig(),
            reference=ReferenceConfig.eager(),
            metadata=MetadataConfig.full(),
            cow=COWConfig.mutable(),
            enable_validation=True,
            validation_mode=ValidationMode.BASIC
        )
    
    # === V8 PRESETS ===
    
    @classmethod
    def v8_smart(cls) -> 'XWDataConfig':
        """
        V8 Smart Mode (Recommended Default).
        
        - Auto-detects file size
        - Partial access for large files
        - Checksums OFF (performance first)
        - All V7 features available
        """
        return cls(
            thresholds=SizeThresholds(),
            integrity=IntegrityConfig(enable_checksums=False),
            partial=PartialAccessConfig.smart(),
            performance=PerformanceConfig.fast()
        )
    
    @classmethod
    def v8_secure(cls) -> 'XWDataConfig':
        """
        V8 Secure Mode (Integrity Focused).
        
        - Checksums enabled (xxh3 for speed)
        - Partial access for large files
        - Strict security settings
        """
        return cls(
            thresholds=SizeThresholds.aggressive(),
            integrity=IntegrityConfig.enabled(),
            partial=PartialAccessConfig.smart(),
            security=SecurityConfig.strict(),
            performance=PerformanceConfig.memory_optimized()
        )
    
    @classmethod
    def v8_performance(cls) -> 'XWDataConfig':
        """
        V8 Performance Mode (Maximum Speed).
        
        - All advanced features OFF
        - Ultra-fast path only
        - V6-level or better performance
        """
        return cls(
            thresholds=SizeThresholds.relaxed(),
            integrity=IntegrityConfig(enable_checksums=False),
            partial=PartialAccessConfig(
                enable_partial_read=False,
                enable_partial_write=False,
                enable_node_streaming=False,
                auto_enable_on_size=False
            ),
            performance=PerformanceConfig.fast(),
            reference=ReferenceConfig(resolution_mode=ReferenceResolutionMode.DISABLED)
        )
    
    # Fluent builders
    def with_security(self, security: SecurityConfig) -> 'XWDataConfig':
        """Set security configuration."""
        self.security = security
        return self
    
    def with_performance(self, performance: PerformanceConfig) -> 'XWDataConfig':
        """Set performance configuration."""
        self.performance = performance
        return self
    
    def with_reference(self, reference: ReferenceConfig) -> 'XWDataConfig':
        """Set reference configuration."""
        self.reference = reference
        return self
    
    def with_metadata(self, metadata: MetadataConfig) -> 'XWDataConfig':
        """Set metadata configuration."""
        self.metadata = metadata
        return self
    
    def with_cow(self, cow: COWConfig) -> 'XWDataConfig':
        """Set COW configuration."""
        self.cow = cow
        return self


# ==============================================================================
# EXPORTS
# ==============================================================================

__all__ = [
    # Component configs
    'SecurityConfig',
    'PerformanceConfig',
    'ReferenceConfig',
    'MetadataConfig',
    'COWConfig',
    
    # Main config
    'XWDataConfig',
]

