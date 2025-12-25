"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: November 2, 2025

Thrift serialization - Apache Thrift RPC framework.

Following I→A→XW pattern:
- I: ISerialization (interface)
- A: ASerialization (abstract base)
- XW: XWThriftSerializer (concrete implementation)
"""

from typing import Any, Optional, Union
from pathlib import Path

from exonware.xwsystem.io.serialization.base import ASerialization
from exonware.xwsystem.io.contracts import EncodeOptions, DecodeOptions
from exonware.xwsystem.io.defs import CodecCapability
from exonware.xwsystem.io.errors import SerializationError
from thrift.protocol import TBinaryProtocol, TCompactProtocol
from thrift.transport import TTransport


class XWThriftSerializer(ASerialization):
    """
    Thrift serializer - follows I→A→XW pattern.
    
    Uses Apache Thrift library.
    """
    
    def __init__(self):
        """Initialize Thrift serializer."""
        super().__init__()
    
    @property
    def codec_id(self) -> str:
        return "thrift"
    
    @property
    def media_types(self) -> list[str]:
        return ["application/x-thrift"]
    
    @property
    def file_extensions(self) -> list[str]:
        return [".thrift"]
    
    @property
    def format_name(self) -> str:
        return "Thrift"
    
    @property
    def mime_type(self) -> str:
        return "application/x-thrift"
    
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
        return ["thrift", "THRIFT"]
    
    def encode(self, value: Any, *, options: Optional[EncodeOptions] = None) -> Union[bytes, str]:
        """Encode Thrift struct to bytes."""
        try:
            trans = TTransport.TMemoryBuffer()
            proto = TBinaryProtocol.TBinaryProtocol(trans)
            value.write(proto)
            return trans.getvalue()
        except Exception as e:
            raise SerializationError(f"Failed to encode Thrift: {e}", self.format_name, e)
    
    def decode(self, repr: Union[bytes, str], *, options: Optional[DecodeOptions] = None) -> Any:
        """Decode Thrift bytes to struct."""
        try:
            opts = options or {}
            thrift_class = opts.get('thrift_class')
            if thrift_class is None:
                raise ValueError("thrift_class required in options")
            
            if isinstance(repr, str):
                repr = repr.encode('utf-8')
            
            trans = TTransport.TMemoryBuffer(repr)
            proto = TBinaryProtocol.TBinaryProtocol(trans)
            obj = thrift_class()
            obj.read(proto)
            return obj
        except Exception as e:
            raise SerializationError(f"Failed to decode Thrift: {e}", self.format_name, e)


ThriftSerializer = XWThriftSerializer

