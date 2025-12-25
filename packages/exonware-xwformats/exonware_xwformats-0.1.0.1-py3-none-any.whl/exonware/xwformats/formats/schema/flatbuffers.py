"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: November 2, 2025

FlatBuffers serialization - Memory-efficient serialization.

Following I→A→XW pattern:
- I: ISerialization (interface)
- A: ASerialization (abstract base)
- XW: XWFlatBuffersSerializer (concrete implementation)
"""

from typing import Any, Optional, Union
from pathlib import Path

from exonware.xwsystem.io.serialization.base import ASerialization
from exonware.xwsystem.io.contracts import EncodeOptions, DecodeOptions
from exonware.xwsystem.io.defs import CodecCapability
from exonware.xwsystem.io.errors import SerializationError
import flatbuffers


class XWFlatBuffersSerializer(ASerialization):
    """
    FlatBuffers serializer - follows I→A→XW pattern.
    
    Uses flatbuffers library.
    """
    
    def __init__(self):
        """Initialize FlatBuffers serializer."""
        super().__init__()
    
    @property
    def codec_id(self) -> str:
        return "flatbuffers"
    
    @property
    def media_types(self) -> list[str]:
        return ["application/flatbuffers"]
    
    @property
    def file_extensions(self) -> list[str]:
        return [".fb", ".fbs"]
    
    @property
    def format_name(self) -> str:
        return "FlatBuffers"
    
    @property
    def mime_type(self) -> str:
        return "application/flatbuffers"
    
    @property
    def is_binary_format(self) -> bool:
        return True
    
    @property
    def supports_streaming(self) -> bool:
        return False
    
    @property
    def capabilities(self) -> CodecCapability:
        return CodecCapability.BIDIRECTIONAL | CodecCapability.SCHEMA
    
    @property
    def aliases(self) -> list[str]:
        return ["flatbuffers", "fb"]
    
    def encode(self, value: Any, *, options: Optional[EncodeOptions] = None) -> Union[bytes, str]:
        """Encode FlatBuffers data to bytes."""
        try:
            # Requires builder instance
            if hasattr(value, 'Output'):
                return value.Output()
            raise TypeError("Value must be a FlatBuffers builder or have Output() method")
        except Exception as e:
            raise SerializationError(f"Failed to encode FlatBuffers: {e}", self.format_name, e)
    
    def decode(self, repr: Union[bytes, str], *, options: Optional[DecodeOptions] = None) -> Any:
        """Decode FlatBuffers bytes to data."""
        try:
            opts = options or {}
            root_type = opts.get('root_type')
            if root_type is None:
                raise ValueError("root_type required for FlatBuffers decoding")
            
            if isinstance(repr, str):
                repr = repr.encode('utf-8')
            
            return root_type.GetRootAs(repr, 0)
        except Exception as e:
            raise SerializationError(f"Failed to decode FlatBuffers: {e}", self.format_name, e)


FlatBuffersSerializer = XWFlatBuffersSerializer

