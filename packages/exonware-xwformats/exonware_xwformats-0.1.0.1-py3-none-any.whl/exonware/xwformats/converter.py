#!/usr/bin/env python3
#exonware/xwformats/src/exonware/xwformats/converter.py
"""
Format Conversion Utility

Optimized format conversion with caching and direct conversions where possible.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 15-Nov-2025

Priority 1 (Security): Safe format conversion
Priority 2 (Usability): Simple conversion API
Priority 3 (Maintainability): Clean conversion logic
Priority 4 (Performance): Optimized conversions with caching
Priority 5 (Extensibility): Easy to add new conversion paths
"""

from typing import Any, Optional, Union
from pathlib import Path

from exonware.xwsystem.io.codec.registry import get_registry
from exonware.xwsystem.io.errors import SerializationError


class FormatConverter:
    """
    Optimized format converter with direct conversion paths.
    
    Provides efficient format conversion with:
    - Direct conversion paths (avoiding intermediate formats)
    - Conversion result caching
    - Lazy serializer instantiation
    """
    
    def __init__(self):
        """Initialize format converter."""
        self._registry = get_registry()
        self._cache = {}  # Simple cache for conversion results
    
    def convert(
        self,
        data: Union[bytes, Any],
        from_format: str,
        to_format: str,
        options: Optional[dict] = None
    ) -> Union[bytes, Any]:
        """
        Convert data from one format to another.
        
        Args:
            data: Input data (bytes or decoded data)
            from_format: Source format codec_id
            to_format: Target format codec_id
            options: Conversion options
            
        Returns:
            Converted data (bytes for binary formats, native for text)
            
        Raises:
            SerializationError: If conversion fails
        """
        options = options or {}
        use_cache = options.get('cache', True)
        
        # Check cache
        cache_key = (id(data), from_format, to_format)
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            # Get serializers
            from_serializer = self._registry.get_serializer(from_format)
            to_serializer = self._registry.get_serializer(to_format)
            
            if from_serializer is None:
                raise SerializationError(f"Unknown source format: {from_format}")
            if to_serializer is None:
                raise SerializationError(f"Unknown target format: {to_format}")
            
            # Optimize: Direct conversion paths
            if from_format == to_format:
                # Same format - return as-is
                result = data
            elif self._has_direct_conversion(from_format, to_format):
                # Direct conversion available
                result = self._direct_convert(data, from_format, to_format, options)
            else:
                # Standard decode-encode path
                # Decode from source format
                if isinstance(data, bytes):
                    decoded = from_serializer.decode(data, options=options)
                else:
                    decoded = data
                
                # Encode to target format
                result = to_serializer.encode(decoded, options=options)
            
            # Cache result
            if use_cache:
                self._cache[cache_key] = result
            
            return result
        except Exception as e:
            raise SerializationError(f"Format conversion failed: {e}") from e
    
    def convert_file(
        self,
        input_path: Union[str, Path],
        output_path: Union[str, Path],
        from_format: Optional[str] = None,
        to_format: Optional[str] = None,
        options: Optional[dict] = None
    ) -> None:
        """
        Convert file from one format to another.
        
        Args:
            input_path: Path to input file
            output_path: Path to output file
            from_format: Source format (auto-detect if None)
            to_format: Target format (auto-detect from extension if None)
            options: Conversion options
        """
        input_path = Path(input_path)
        output_path = Path(output_path)
        
        # Auto-detect formats from extensions
        if from_format is None:
            from_format = self._detect_format_from_extension(input_path.suffix)
        if to_format is None:
            to_format = self._detect_format_from_extension(output_path.suffix)
        
        # Read input file
        input_data = input_path.read_bytes()
        
        # Convert
        output_data = self.convert(input_data, from_format, to_format, options)
        
        # Write output file
        if isinstance(output_data, bytes):
            output_path.write_bytes(output_data)
        else:
            output_path.write_text(str(output_data), encoding='utf-8')
    
    def _has_direct_conversion(self, from_format: str, to_format: str) -> bool:
        """Check if direct conversion path exists."""
        # Direct conversions (avoiding decode-encode overhead)
        direct_paths = {
            ('json', 'yaml'): True,
            ('yaml', 'json'): True,
            ('json', 'toml'): True,
            ('toml', 'json'): True,
            ('csv', 'json'): True,
            ('json', 'csv'): True,
        }
        return direct_paths.get((from_format, to_format), False)
    
    def _direct_convert(
        self,
        data: Union[bytes, Any],
        from_format: str,
        to_format: str,
        options: Optional[dict] = None
    ) -> Union[bytes, Any]:
        """Perform direct conversion (optimized path)."""
        from_serializer = self._registry.get_serializer(from_format)
        to_serializer = self._registry.get_serializer(to_format)
        
        # For now, use standard decode-encode
        # Direct conversions can be optimized later
        if isinstance(data, bytes):
            decoded = from_serializer.decode(data, options=options)
        else:
            decoded = data
        
        return to_serializer.encode(decoded, options=options)
    
    def _detect_format_from_extension(self, extension: str) -> str:
        """Detect format from file extension."""
        extension_map = {
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.toml': 'toml',
            '.csv': 'csv',
            '.xml': 'xml',
            '.bson': 'bson',
            '.ubjson': 'ubjson',
            '.pb': 'protobuf',
            '.proto': 'protobuf',
            '.parquet': 'parquet',
            '.avro': 'avro',
            '.thrift': 'thrift',
            '.orc': 'orc',
            '.h5': 'hdf5',
            '.hdf5': 'hdf5',
            '.nc': 'netcdf',
            '.mat': 'mat',
            '.feather': 'feather',
            '.zarr': 'zarr',
        }
        return extension_map.get(extension.lower(), 'json')  # Default to JSON
    
    def clear_cache(self) -> None:
        """Clear conversion cache."""
        self._cache.clear()


# Global converter instance
_converter = None

def get_converter() -> FormatConverter:
    """Get global format converter instance."""
    global _converter
    if _converter is None:
        _converter = FormatConverter()
    return _converter

