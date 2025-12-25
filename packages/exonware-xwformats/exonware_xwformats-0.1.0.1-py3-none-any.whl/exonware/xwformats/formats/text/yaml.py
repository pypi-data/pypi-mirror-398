#!/usr/bin/env python3
#exonware/xwformats/src/exonware/xwformats/formats/text/yaml.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 15-Nov-2025

YAML Serialization - YAML Ain't Markup Language

YAML is a human-readable data serialization format:
- Human-readable syntax
- Supports complex data structures
- Widely used for configuration files
- JSON-compatible subset

Priority 1 (Security): Safe YAML loading (prevent code execution)
Priority 2 (Usability): Simple YAML read/write API
Priority 3 (Maintainability): Clean YAML handling
Priority 4 (Performance): Efficient YAML parsing
Priority 5 (Extensibility): Support YAML 1.1 and 1.2
"""

from typing import Any, Optional, Union
from pathlib import Path

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    try:
        import ruamel.yaml as yaml
        YAML_AVAILABLE = True
    except ImportError:
        YAML_AVAILABLE = False
        yaml = None

from exonware.xwsystem.io.serialization.base import ASerialization
from exonware.xwsystem.io.serialization.contracts import ISerialization
from exonware.xwsystem.io.contracts import EncodeOptions, DecodeOptions
from exonware.xwsystem.io.errors import SerializationError


class XWYamlSerializer(ASerialization):
    """
    YAML serializer.
    
    I: ISerialization (interface)
    A: ASerialization (abstract base)
    XW: XWYamlSerializer (concrete implementation)
    """
    
    def __init__(self):
        """Initialize YAML serializer."""
        super().__init__()
        if not YAML_AVAILABLE:
            raise ImportError(
                "yaml library not available. Install with: pip install pyyaml"
            )
    
    @property
    def codec_id(self) -> str:
        """Codec identifier."""
        return "yaml"
    
    @property
    def media_types(self) -> list[str]:
        """Supported media types."""
        return ["text/yaml", "application/yaml", "text/x-yaml"]
    
    @property
    def file_extensions(self) -> list[str]:
        """Supported file extensions."""
        return [".yaml", ".yml"]
    
    @property
    def format_name(self) -> str:
        """Format name."""
        return "YAML"
    
    @property
    def mime_type(self) -> str:
        """MIME type."""
        return "text/yaml"
    
    @property
    def is_binary_format(self) -> bool:
        """Whether format is binary."""
        return False
    
    @property
    def supports_streaming(self) -> bool:
        """Whether format supports streaming."""
        return True
    
    def encode(
        self,
        data: Any,
        options: Optional[EncodeOptions] = None
    ) -> bytes:
        """
        Encode data to YAML.
        
        Args:
            data: Data to encode
            options: Encoding options (default_flow_style, allow_unicode, etc.)
            
        Returns:
            YAML-encoded bytes
            
        Raises:
            SerializationError: If encoding fails
        """
        if not YAML_AVAILABLE:
            raise SerializationError("yaml library not available")
        
        options = options or {}
        default_flow_style = options.get('default_flow_style', False)
        allow_unicode = options.get('allow_unicode', True)
        sort_keys = options.get('sort_keys', False)
        
        try:
            yaml_str = yaml.dump(
                data,
                default_flow_style=default_flow_style,
                allow_unicode=allow_unicode,
                sort_keys=sort_keys,
                Dumper=yaml.SafeDumper if hasattr(yaml, 'SafeDumper') else yaml.dump
            )
            return yaml_str.encode('utf-8')
        except Exception as e:
            raise SerializationError(f"YAML encoding failed: {e}") from e
    
    def decode(
        self,
        data: Union[bytes, bytearray, str],
        options: Optional[DecodeOptions] = None
    ) -> Any:
        """
        Decode YAML data.
        
        Args:
            data: YAML-encoded bytes or string
            options: Decoding options
            
        Returns:
            Decoded data
            
        Raises:
            SerializationError: If decoding fails
        """
        if not YAML_AVAILABLE:
            raise SerializationError("yaml library not available")
        
        try:
            if isinstance(data, (bytes, bytearray)):
                data = data.decode('utf-8')
            
            # Use SafeLoader to prevent code execution
            return yaml.load(
                data,
                Loader=yaml.SafeLoader if hasattr(yaml, 'SafeLoader') else yaml.load
            )
        except Exception as e:
            raise SerializationError(f"YAML decoding failed: {e}") from e
    
    def encode_to_file(
        self,
        data: Any,
        file_path: Union[str, Path],
        options: Optional[EncodeOptions] = None
    ) -> None:
        """
        Encode data to YAML file.
        
        Args:
            data: Data to encode
            file_path: Path to output file
            options: Encoding options
        """
        yaml_data = self.encode(data, options)
        file_path = Path(file_path)
        file_path.write_bytes(yaml_data)
    
    def decode_from_file(
        self,
        file_path: Union[str, Path],
        options: Optional[DecodeOptions] = None
    ) -> Any:
        """
        Decode YAML from file.
        
        Args:
            file_path: Path to YAML file
            options: Decoding options
            
        Returns:
            Decoded data
        """
        file_path = Path(file_path)
        yaml_data = file_path.read_bytes()
        return self.decode(yaml_data, options)

