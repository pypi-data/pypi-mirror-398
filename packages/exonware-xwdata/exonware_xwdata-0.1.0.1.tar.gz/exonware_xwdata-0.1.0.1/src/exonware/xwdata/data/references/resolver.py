#!/usr/bin/env python3
"""
#exonware/xwdata/src/exonware/xwdata/data/references/resolver.py

Reference Resolver Implementation

Resolves cross-references by loading external files.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 26-Oct-2025
"""

from typing import Any, Optional
from pathlib import Path
import asyncio
import urllib.parse
from exonware.xwsystem import get_logger

from ...base import AReferenceResolver
from ...config import XWDataConfig
from ...contracts import IFormatStrategy
from ...errors import XWDataReferenceError, XWDataCircularReferenceError
from .detector import ReferenceDetector

logger = get_logger(__name__)


class ReferenceResolver(AReferenceResolver):
    """
    Reference resolver with circular dependency detection.
    
    Features:
    - Loads external referenced files
    - Detects circular references
    - Caches resolved references
    - Respects security constraints
    """
    
    def __init__(self, config: Optional[XWDataConfig] = None):
        """
        Initialize reference resolver.
        
        Args:
            config: Optional configuration
        """
        super().__init__()
        self._config = config or XWDataConfig.default()
        self._detector = ReferenceDetector()
    
    async def resolve(
        self,
        data: Any,
        strategy: IFormatStrategy,
        base_path: Optional[Path] = None,
        **opts
    ) -> Any:
        """
        Resolve all references in data.
        
        Args:
            data: Data with references
            strategy: Format strategy
            base_path: Base path for relative references
            **opts: Additional options
            
        Returns:
            Data with resolved references
            
        Root cause fixed: Stub implementation returned data unchanged.
        Solution: Full recursive resolution with file loading, JSON Pointer, caching.
        Priority: Security #1 - Path validation, scheme check, size limits
        Priority: Usability #2 - Clear error messages for missing references
        """
        # Detect references
        references = await self._detector.detect(data, strategy, **opts)
        
        if not references:
            return data
        
        # Check circular references first
        if self._config.reference.enable_circular_detection:
            self._check_circular_references(references)
        
        logger.debug(f"Detected {len(references)} references - resolving...")
        
        # Resolve all references recursively
        visited: set[str] = set()
        resolved_data = await self._resolve_recursive(
            data=data,
            strategy=strategy,
            base_path=base_path,
            resolution_stack=[],
            depth=0,
            **opts
        )
        
        logger.info(f"Successfully resolved {len(references)} references")
        return resolved_data
    
    async def resolve_reference(
        self,
        reference: dict[str, Any],
        base_path: Optional[Path] = None,
        **opts
    ) -> Any:
        """
        Resolve single reference.
        
        Args:
            reference: Reference to resolve
            base_path: Base path for relative references
            **opts: Additional options
            
        Returns:
            Resolved data
            
        Root cause fixed: Placeholder implementation that returned {'$ref': uri}.
        Solution: Full file loading with JSON Pointer, caching, security.
        Priority: Security #1 - Path/scheme validation, timeout, size limits
        """
        uri = reference.get('uri', '')
        ref_type = reference.get('type', 'file')
        
        # Check cache first
        if self._config.reference.cache_resolved:
            cache_key = f"ref:{uri}"
            if cache_key in self._resolution_cache:
                logger.debug(f"Cache hit for reference: {uri}")
                return self._resolution_cache[cache_key]
        
        # Check circular references
        if uri in self._resolution_stack:
            cycle = self._resolution_stack + [uri]
            raise XWDataCircularReferenceError(
                f"Circular reference detected: {uri}",
                cycle=cycle,
                reference=uri
            )
        
        # Add to resolution stack
        self._resolution_stack.append(uri)
        
        try:
            # Parse URI
            parsed = urllib.parse.urlparse(uri)
            scheme = parsed.scheme if parsed.scheme else 'file'
            fragment = parsed.fragment  # JSON Pointer or anchor
            
            # Security: Validate scheme
            if self._config.reference.enable_scheme_validation:
                if scheme not in self._config.reference.allowed_schemes:
                    raise XWDataReferenceError(
                        f"Unsupported URI scheme: {scheme}. Allowed: {self._config.reference.allowed_schemes}",
                        reference=uri
                    )
            
            # Load external file or content
            if ref_type == 'json_pointer' or '#' in uri:
                # JSON Pointer reference like "$ref": "#/definitions/Pet"
                resolved_data = await self._resolve_json_pointer(uri, fragment, base_path, **opts)
            else:
                # File reference like "$ref": "common.json"
                resolved_data = await self._load_external_file(uri, base_path, **opts)
            
            # Cache result
            if self._config.reference.cache_resolved:
                cache_key = f"ref:{uri}"
                self._resolution_cache[cache_key] = resolved_data
            
            logger.debug(f"Successfully resolved reference: {uri}")
            return resolved_data
            
        except XWDataReferenceError:
            raise  # Re-raise reference errors
        except Exception as e:
            raise XWDataReferenceError(
                f"Failed to resolve reference: {uri} - {str(e)}",
                reference=uri
            )
        finally:
            # Remove from resolution stack
            if uri in self._resolution_stack:
                self._resolution_stack.remove(uri)
    
    def _check_circular_references(self, references: list[dict[str, Any]]) -> None:
        """
        Check for circular references.
        
        Args:
            references: List of references to check
        """
        # Build reference graph
        ref_uris = [ref.get('uri') for ref in references if 'uri' in ref]
        
        # Simple check: look for self-references
        if len(ref_uris) != len(set(ref_uris)):
            duplicates = [uri for uri in ref_uris if ref_uris.count(uri) > 1]
            logger.warning(f"Potential circular references detected: {duplicates}")
    
    async def _resolve_recursive(
        self,
        data: Any,
        strategy: IFormatStrategy,
        base_path: Optional[Path],
        resolution_stack: list[str],
        depth: int,
        **opts
    ) -> Any:
        """
        Recursively resolve references in data structure.
        
        Args:
            data: Data to process
            strategy: Format strategy
            base_path: Base path for relative references
            resolution_stack: Current resolution path (for circular detection)
            depth: Current recursion depth
            **opts: Additional options
            
        Returns:
            Data with resolved references
        """
        # Check max depth
        if depth > self._config.reference.max_resolution_depth:
            raise XWDataReferenceError(
                f"Max resolution depth exceeded: {self._config.reference.max_resolution_depth}",
                reference=f"depth={depth}"
            )
        
        # Handle dict
        if isinstance(data, dict):
            # Check for $ref key (JSON reference)
            if '$ref' in data:
                ref_uri = data['$ref']
                
                # Check for circular reference in current resolution path
                if ref_uri in resolution_stack:
                    # Circular reference detected!
                    cycle = resolution_stack + [ref_uri]
                    raise XWDataCircularReferenceError(
                        f"Circular reference detected: {ref_uri}",
                        cycle=cycle,
                        reference=ref_uri
                    )
                
                # Add to resolution stack
                resolution_stack.append(ref_uri)
                try:
                    reference = {'uri': ref_uri, 'type': 'json_pointer' if '#' in ref_uri else 'file'}
                    resolved = await self.resolve_reference(reference, base_path, **opts)
                    # Recursively resolve the resolved data
                    return await self._resolve_recursive(resolved, strategy, base_path, resolution_stack, depth + 1, **opts)
                finally:
                    # Remove from resolution stack
                    resolution_stack.pop()
            
            # Recursively process dict values
            resolved_dict = {}
            for key, value in data.items():
                resolved_dict[key] = await self._resolve_recursive(value, strategy, base_path, resolution_stack, depth + 1, **opts)
            return resolved_dict
        
        # Handle list
        elif isinstance(data, list):
            resolved_list = []
            for item in data:
                resolved_list.append(await self._resolve_recursive(item, strategy, base_path, resolution_stack, depth + 1, **opts))
            return resolved_list
        
        # Primitive types - return as-is
        else:
            return data
    
    async def _load_external_file(
        self,
        uri: str,
        base_path: Optional[Path] = None,
        **opts
    ) -> Any:
        """
        Load external file referenced by URI.
        
        Args:
            uri: URI to load
            base_path: Base path for relative URIs
            **opts: Additional options
            
        Returns:
            Loaded data
            
        Security: Path validation, size limits, timeout
        """
        # Parse URI
        parsed = urllib.parse.urlparse(uri)
        scheme = parsed.scheme if parsed.scheme else 'file'
        
        # Handle file:// or relative file paths
        if scheme == 'file' or not parsed.scheme:
            # Get file path
            if parsed.scheme == 'file':
                file_path = Path(urllib.parse.unquote(parsed.path))
            else:
                file_path = Path(uri.split('#')[0])  # Remove fragment
            
            # Make absolute if relative
            if not file_path.is_absolute() and base_path:
                file_path = base_path / file_path
            
            # Security: Validate path
            if self._config.reference.enable_path_validation:
                from exonware.xwsystem.security import PathValidator
                validator = PathValidator()
                try:
                    validator.validate_path(str(file_path), for_writing=False, create_dirs=False)
                except Exception as e:
                    raise XWDataReferenceError(
                        f"Path validation failed for reference: {uri} - {str(e)}",
                        reference=uri
                    )
            
            # Check file exists
            if not file_path.exists():
                raise XWDataReferenceError(
                    f"Referenced file not found: {file_path}",
                    reference=uri
                )
            
            # Security: Check file size
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            if file_size_mb > self._config.reference.max_external_size_mb:
                raise XWDataReferenceError(
                    f"Referenced file exceeds size limit: {file_size_mb:.2f}MB > {self._config.reference.max_external_size_mb}MB",
                    reference=uri
                )
            
            # Load file using XWData engine
            try:
                # Import here to avoid circular dependency
                from ...data.engine import XWDataEngine
                engine = XWDataEngine(config=self._config)
                
                # Load file
                result = await engine.load(file_path, **opts)
                # XWDataNode - get native data
                return result.to_native()
            
            except Exception as e:
                raise XWDataReferenceError(
                    f"Failed to load referenced file: {file_path} - {str(e)}",
                    reference=uri
                )
        
        # Handle https:// URLs
        elif scheme == 'https':
            if not self._config.reference.follow_external:
                raise XWDataReferenceError(
                    f"External references are disabled: {uri}",
                    reference=uri
                )
            
            # Load URL with timeout
            try:
                import aiohttp
                
                timeout = aiohttp.ClientTimeout(total=self._config.reference.timeout_seconds)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(uri) as response:
                        response.raise_for_status()
                        
                        # Check content length
                        content_length = response.headers.get('Content-Length')
                        if content_length:
                            size_mb = int(content_length) / (1024 * 1024)
                            if size_mb > self._config.reference.max_external_size_mb:
                                raise XWDataReferenceError(
                                    f"External reference exceeds size limit: {size_mb:.2f}MB > {self._config.reference.max_external_size_mb}MB",
                                    reference=uri
                                )
                        
                        # Read content
                        content = await response.read()
                        
                        # Parse based on content type
                        content_type = response.headers.get('Content-Type', '')
                        if 'json' in content_type:
                            import json
                            return json.loads(content)
                        elif 'yaml' in content_type or 'yml' in uri:
                            import yaml
                            return yaml.safe_load(content)
                        else:
                            # Try JSON first, then YAML
                            try:
                                import json
                                return json.loads(content)
                            except:
                                import yaml
                                return yaml.safe_load(content)
            
            except asyncio.TimeoutError:
                raise XWDataReferenceError(
                    f"Timeout loading external reference: {uri}",
                    reference=uri
                )
            except Exception as e:
                raise XWDataReferenceError(
                    f"Failed to load external reference: {uri} - {str(e)}",
                    reference=uri
                )
        
        else:
            raise XWDataReferenceError(
                f"Unsupported URI scheme: {scheme}",
                reference=uri
            )
    
    async def _resolve_json_pointer(
        self,
        uri: str,
        fragment: str,
        base_path: Optional[Path] = None,
        **opts
    ) -> Any:
        """
        Resolve JSON Pointer reference.
        
        Args:
            uri: Full URI with fragment
            fragment: Fragment part (after #)
            base_path: Base path for relative references
            **opts: Additional options
            
        Returns:
            Resolved data at pointer location
            
        Implements: RFC 6901 JSON Pointer
        """
        # Extract file part (before #)
        file_part = uri.split('#')[0]
        
        # If file part is empty, it's a reference to current document
        if not file_part:
            # This would require access to current document
            # For now, raise an error - this should be handled at higher level
            raise XWDataReferenceError(
                f"JSON Pointer to current document not supported in this context: {uri}",
                reference=uri
            )
        
        # Load the file first
        data = await self._load_external_file(file_part, base_path, **opts)
        
        # Parse JSON Pointer fragment
        if not fragment or fragment == '/':
            return data
        
        # Split pointer into parts
        pointer_parts = fragment.split('/')[1:]  # Skip first empty element
        
        # Navigate through data structure
        current = data
        for part in pointer_parts:
            # Decode special characters
            part = part.replace('~1', '/').replace('~0', '~')
            
            if isinstance(current, dict):
                if part not in current:
                    raise XWDataReferenceError(
                        f"JSON Pointer path not found: {fragment} in {file_part}",
                        reference=uri
                    )
                current = current[part]
            
            elif isinstance(current, list):
                try:
                    index = int(part)
                    if index < 0 or index >= len(current):
                        raise XWDataReferenceError(
                            f"JSON Pointer index out of range: {index} in {fragment}",
                            reference=uri
                        )
                    current = current[index]
                except ValueError:
                    raise XWDataReferenceError(
                        f"Invalid JSON Pointer array index: {part} in {fragment}",
                        reference=uri
                    )
            
            else:
                raise XWDataReferenceError(
                    f"JSON Pointer navigation failed at: {part} in {fragment}",
                    reference=uri
                )
        
        return current


__all__ = ['ReferenceResolver']

