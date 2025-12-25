"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: November 2, 2025

Protocol Buffers serialization - Google's data interchange format.

Following I→A→XW pattern:
- I: ISerialization (interface)
- A: ASerialization (abstract base)
- XW: XWProtobufSerializer (concrete implementation)
"""

from typing import Any, Optional, Union
from pathlib import Path

from exonware.xwsystem.io.serialization.base import ASerialization
from exonware.xwsystem.io.contracts import EncodeOptions, DecodeOptions
from exonware.xwsystem.io.defs import CodecCapability
from exonware.xwsystem.io.errors import SerializationError
from google.protobuf import message, json_format


class XWProtobufSerializer(ASerialization):
    """
    Protocol Buffers serializer - follows I→A→XW pattern.
    
    I: ISerialization (interface)
    A: ASerialization (abstract base)
    XW: XWProtobufSerializer (concrete implementation)
    
    Uses google.protobuf library.
    
    Examples:
        >>> serializer = XWProtobufSerializer()
        >>> 
        >>> # Encode protobuf message
        >>> proto_bytes = serializer.encode(message_instance)
        >>> 
        >>> # Decode to message
        >>> msg = serializer.decode(proto_bytes, options={'message_type': MyMessage})
    """
    
    def __init__(self):
        """Initialize Protobuf serializer."""
        super().__init__()
    
    # ========================================================================
    # CODEC METADATA
    # ========================================================================
    
    @property
    def codec_id(self) -> str:
        return "protobuf"
    
    @property
    def media_types(self) -> list[str]:
        return ["application/protobuf", "application/x-protobuf"]
    
    @property
    def file_extensions(self) -> list[str]:
        return [".proto", ".pb"]
    
    @property
    def format_name(self) -> str:
        return "Protobuf"
    
    @property
    def mime_type(self) -> str:
        return "application/protobuf"
    
    @property
    def is_binary_format(self) -> bool:
        return True  # Protobuf is binary
    
    @property
    def supports_streaming(self) -> bool:
        return True  # Protobuf supports streaming
    
    @property
    def capabilities(self) -> CodecCapability:
        return CodecCapability.BIDIRECTIONAL | CodecCapability.SCHEMA
    
    @property
    def aliases(self) -> list[str]:
        return ["protobuf", "proto", "pb"]
    
    @property
    def codec_types(self) -> list[str]:
        """Protobuf is a binary schema format."""
        return ["binary", "schema", "serialization"]
    
    # ========================================================================
    # CORE ENCODE/DECODE (Using google.protobuf)
    # ========================================================================
    
    def encode(self, value: Any, *, options: Optional[EncodeOptions] = None) -> Union[bytes, str]:
        """
        Encode protobuf message to bytes.
        
        Args:
            value: Protobuf message instance
            options: Encoding options
        
        Returns:
            Protobuf bytes
        
        Raises:
            SerializationError: If encoding fails
        """
        try:
            if not isinstance(value, message.Message):
                raise TypeError("Value must be a protobuf Message instance")
            
            # Serialize to bytes
            proto_bytes = value.SerializeToString()
            
            return proto_bytes
            
        except Exception as e:
            raise SerializationError(
                f"Failed to encode Protobuf: {e}",
                format_name=self.format_name,
                original_error=e
            )
    
    def decode(self, repr: Union[bytes, str], *, options: Optional[DecodeOptions] = None) -> Any:
        """
        Decode protobuf bytes to message.
        
        Args:
            repr: Protobuf bytes
            options: Must include 'message_type' with the message class
        
        Returns:
            Protobuf message instance
        
        Raises:
            SerializationError: If decoding fails
        """
        try:
            opts = options or {}
            
            # Requires message_type in options
            message_type = opts.get('message_type')
            if message_type is None:
                raise ValueError("message_type required in options for Protobuf decoding")
            
            # Protobuf requires bytes
            if isinstance(repr, str):
                repr = repr.encode('utf-8')
            
            # Create message instance and parse
            msg = message_type()
            msg.ParseFromString(repr)
            
            return msg
            
        except Exception as e:
            raise SerializationError(
                f"Failed to decode Protobuf: {e}",
                format_name=self.format_name,
                original_error=e
            )


# Backward compatibility alias
ProtobufSerializer = XWProtobufSerializer

