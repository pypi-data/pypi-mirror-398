#!/usr/bin/env python3
#exonware/xwformats/src/exonware/xwformats/formats/binary/bson.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 15-Nov-2025

BSON Serialization - Binary JSON

BSON (Binary JSON) is MongoDB's binary format that:
- Extends JSON with additional data types
- More compact than JSON for some data
- Native support for dates, binary data, ObjectId
- Used by MongoDB for document storage

Priority 1 (Security): Safe binary deserialization
Priority 2 (Usability): JSON-compatible binary format
Priority 3 (Maintainability): Clean binary serialization
Priority 4 (Performance): Fast binary encoding/decoding
Priority 5 (Extensibility): Compatible with MongoDB ecosystem
"""

from typing import Any, Optional, Union
from pathlib import Path

try:
    import bson
    BSON_AVAILABLE = True
except ImportError:
    BSON_AVAILABLE = False
    bson = None

from exonware.xwsystem.io.serialization.base import ASerialization
from exonware.xwsystem.io.serialization.contracts import ISerialization
from exonware.xwsystem.io.contracts import EncodeOptions, DecodeOptions
from exonware.xwsystem.io.errors import SerializationError


class XWBsonSerializer(ASerialization):
    """
    BSON (Binary JSON) serializer.
    
    I: ISerialization (interface)
    A: ASerialization (abstract base)
    XW: XWBsonSerializer (concrete implementation)
    """
    
    def __init__(self):
        """Initialize BSON serializer."""
        super().__init__()
        if not BSON_AVAILABLE:
            raise ImportError(
                "bson library not available. Install with: pip install pymongo"
            )
    
    @property
    def codec_id(self) -> str:
        """Codec identifier."""
        return "bson"
    
    @property
    def media_types(self) -> list[str]:
        """Supported media types."""
        return ["application/bson"]
    
    @property
    def file_extensions(self) -> list[str]:
        """Supported file extensions."""
        return [".bson"]
    
    @property
    def format_name(self) -> str:
        """Format name."""
        return "BSON"
    
    @property
    def mime_type(self) -> str:
        """MIME type."""
        return "application/bson"
    
    @property
    def is_binary_format(self) -> bool:
        """Whether format is binary."""
        return True
    
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
        Encode data to BSON.
        
        Args:
            data: Data to encode (dict, list, or BSON-compatible types)
            options: Encoding options
            
        Returns:
            BSON-encoded bytes
            
        Raises:
            SerializationError: If encoding fails
        """
        if not BSON_AVAILABLE:
            raise SerializationError("bson library not available")
        
        try:
            return bson.encode(data)
        except Exception as e:
            raise SerializationError(f"BSON encoding failed: {e}") from e
    
    def decode(
        self,
        data: Union[bytes, bytearray],
        options: Optional[DecodeOptions] = None
    ) -> Any:
        """
        Decode BSON data.
        
        Args:
            data: BSON-encoded bytes
            options: Decoding options
            
        Returns:
            Decoded data (dict, list, etc.)
            
        Raises:
            SerializationError: If decoding fails
        """
        if not BSON_AVAILABLE:
            raise SerializationError("bson library not available")
        
        try:
            return bson.decode(data)
        except Exception as e:
            raise SerializationError(f"BSON decoding failed: {e}") from e
    
    def encode_to_file(
        self,
        data: Any,
        file_path: Union[str, Path],
        options: Optional[EncodeOptions] = None
    ) -> None:
        """
        Encode data to BSON file.
        
        Args:
            data: Data to encode
            file_path: Path to output file
            options: Encoding options
        """
        bson_data = self.encode(data, options)
        file_path = Path(file_path)
        file_path.write_bytes(bson_data)
    
    def decode_from_file(
        self,
        file_path: Union[str, Path],
        options: Optional[DecodeOptions] = None
    ) -> Any:
        """
        Decode BSON from file.
        
        Args:
            file_path: Path to BSON file
            options: Decoding options
            
        Returns:
            Decoded data
        """
        file_path = Path(file_path)
        bson_data = file_path.read_bytes()
        return self.decode(bson_data, options)

