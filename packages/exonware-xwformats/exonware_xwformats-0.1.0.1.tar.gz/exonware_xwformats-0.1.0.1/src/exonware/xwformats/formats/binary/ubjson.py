#!/usr/bin/env python3
#exonware/xwformats/src/exonware/xwformats/formats/binary/ubjson.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 02-Nov-2025

UBJSON Serialization - Universal Binary JSON

UBJSON is a binary JSON format that:
- Maintains JSON data model
- More compact than JSON
- Faster than MessagePack for some data
- Type markers for efficiency

Priority 1 (Security): Safe binary deserialization
Priority 2 (Usability): JSON-compatible binary format
Priority 3 (Maintainability): Clean binary serialization
Priority 4 (Performance): Fast binary encoding/decoding
Priority 5 (Extensibility): Compatible with JSON ecosystem
"""

from typing import Any, Optional, Union
from pathlib import Path

import ubjson

from exonware.xwsystem.io.serialization.base import ASerialization
from exonware.xwsystem.io.serialization.contracts import ISerialization


class XWUbjsonSerializer(ASerialization):
    """
    UBJSON (Universal Binary JSON) serializer.
    
    I: ISerialization (interface)
    A: ASerialization (abstract base)
    XW: XWUbjsonSerializer (concrete implementation)
    """
    
    def __init__(self):
        """Initialize UBJSON serializer."""
        super().__init__()
    
    @property
    def codec_id(self) -> str:
        """Codec identifier."""
        return "ubjson"
    
    @property
    def media_types(self) -> list[str]:
        """Supported MIME types."""
        return ["application/ubjson"]
    
    @property
    def file_extensions(self) -> list[str]:
        """Supported file extensions."""
        return [".ubj", ".ubjson"]
    
    @property
    def aliases(self) -> list[str]:
        """Alternative names."""
        return ["ubjson", "UBJSON", "ubj"]
    
    @property
    def codec_types(self) -> list[str]:
        """UBJSON is a binary serialization format."""
        return ["binary", "serialization"]
    
    def encode(self, data: Any, options: Optional[dict[str, Any]] = None) -> bytes:
        """
        Encode data to UBJSON bytes.
        
        Args:
            data: Data to encode
            options: Encoding options
            
        Returns:
            UBJSON bytes
        """
        return ubjson.dumpb(data)
    
    def decode(self, data: bytes, options: Optional[dict[str, Any]] = None) -> Any:
        """
        Decode UBJSON bytes to Python data.
        
        Args:
            data: UBJSON bytes
            options: Decoding options
            
        Returns:
            Decoded Python data
        """
        return ubjson.loadb(data)


# Backward compatibility alias
UbjsonSerializer = XWUbjsonSerializer

