"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: November 2, 2025

Cap'n Proto serialization - Fast data interchange format.

Following I→A→XW pattern:
- I: ISerialization (interface)
- A: ASerialization (abstract base)
- XW: XWCapnProtoSerializer (concrete implementation)
"""

from typing import Any, Optional, Union
from pathlib import Path

from exonware.xwsystem.io.serialization.base import ASerialization
from exonware.xwsystem.io.contracts import EncodeOptions, DecodeOptions
from exonware.xwsystem.io.defs import CodecCapability
from exonware.xwsystem.io.errors import SerializationError
import capnp


class XWCapnProtoSerializer(ASerialization):
    """
    Cap'n Proto serializer - follows I→A→XW pattern.
    
    Uses pycapnp library.
    """
    
    def __init__(self):
        """Initialize Cap'n Proto serializer."""
        super().__init__()
    
    @property
    def codec_id(self) -> str:
        return "capnproto"
    
    @property
    def media_types(self) -> list[str]:
        return ["application/capnproto"]
    
    @property
    def file_extensions(self) -> list[str]:
        return [".capnp"]
    
    @property
    def format_name(self) -> str:
        return "Cap'n Proto"
    
    @property
    def mime_type(self) -> str:
        return "application/capnproto"
    
    @property
    def is_binary_format(self) -> bool:
        return True
    
    @property
    def supports_streaming(self) -> bool:
        return True
    
    @property
    def capabilities(self) -> CodecCapability:
        return CodecCapability.BIDIRECTIONAL | CodecCapability.SCHEMA
    
    @property
    def aliases(self) -> list[str]:
        return ["capnproto", "capnp"]
    
    def encode(self, value: Any, *, options: Optional[EncodeOptions] = None) -> Union[bytes, str]:
        """Encode Cap'n Proto message to bytes."""
        try:
            return value.to_bytes()
        except Exception as e:
            raise SerializationError(f"Failed to encode Cap'n Proto: {e}", self.format_name, e)
    
    def decode(self, repr: Union[bytes, str], *, options: Optional[DecodeOptions] = None) -> Any:
        """Decode Cap'n Proto bytes to message."""
        try:
            opts = options or {}
            schema = opts.get('schema')
            if schema is None:
                raise ValueError("schema required for Cap'n Proto decoding")
            
            if isinstance(repr, str):
                repr = repr.encode('utf-8')
            
            return schema.from_bytes(repr)
        except Exception as e:
            raise SerializationError(f"Failed to decode Cap'n Proto: {e}", self.format_name, e)


CapnProtoSerializer = XWCapnProtoSerializer

