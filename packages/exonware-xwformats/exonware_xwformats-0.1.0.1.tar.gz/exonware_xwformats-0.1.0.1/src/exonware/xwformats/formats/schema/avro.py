"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: November 2, 2025

Avro serialization - Apache Avro data serialization.

Following I→A→XW pattern:
- I: ISerialization (interface)
- A: ASerialization (abstract base)
- XW: XWAvroSerializer (concrete implementation)
"""

import io
from typing import Any, Optional, Union
from pathlib import Path

from exonware.xwsystem.io.serialization.base import ASerialization
from exonware.xwsystem.io.contracts import EncodeOptions, DecodeOptions
from exonware.xwsystem.io.defs import CodecCapability
from exonware.xwsystem.io.errors import SerializationError
import fastavro


class XWAvroSerializer(ASerialization):
    """
    Avro serializer - follows I→A→XW pattern.
    
    I: ISerialization (interface)
    A: ASerialization (abstract base)
    XW: XWAvroSerializer (concrete implementation)
    
    Uses fastavro library for Apache Avro serialization.
    
    Examples:
        >>> serializer = XWAvroSerializer()
        >>> 
        >>> schema = {
        ...     "type": "record",
        ...     "name": "User",
        ...     "fields": [
        ...         {"name": "name", "type": "string"},
        ...         {"name": "age", "type": "int"}
        ...     ]
        ... }
        >>> 
        >>> # Encode with schema
        >>> avro_bytes = serializer.encode(
        ...     {"name": "John", "age": 30},
        ...     options={"schema": schema}
        ... )
        >>> 
        >>> # Decode with schema
        >>> data = serializer.decode(avro_bytes, options={"schema": schema})
    """
    
    def __init__(self):
        """Initialize Avro serializer."""
        super().__init__()
    
    # ========================================================================
    # CODEC METADATA
    # ========================================================================
    
    @property
    def codec_id(self) -> str:
        return "avro"
    
    @property
    def media_types(self) -> list[str]:
        return ["application/avro", "avro/binary"]
    
    @property
    def file_extensions(self) -> list[str]:
        return [".avro"]
    
    @property
    def format_name(self) -> str:
        return "Avro"
    
    @property
    def mime_type(self) -> str:
        return "application/avro"
    
    @property
    def is_binary_format(self) -> bool:
        return True  # Avro is binary
    
    @property
    def supports_streaming(self) -> bool:
        return True  # Avro supports streaming
    
    @property
    def capabilities(self) -> CodecCapability:
        return CodecCapability.BIDIRECTIONAL | CodecCapability.SCHEMA
    
    @property
    def aliases(self) -> list[str]:
        return ["avro", "AVRO"]
    
    # ========================================================================
    # CORE ENCODE/DECODE (Using fastavro)
    # ========================================================================
    
    def encode(self, value: Any, *, options: Optional[EncodeOptions] = None) -> Union[bytes, str]:
        """
        Encode data to Avro bytes.
        
        Uses fastavro.schemaless_writer().
        
        Args:
            value: Data to serialize
            options: Must include 'schema' with Avro schema
        
        Returns:
            Avro bytes
        
        Raises:
            SerializationError: If encoding fails
        """
        try:
            opts = options or {}
            
            # Requires schema
            schema = opts.get('schema')
            if schema is None:
                raise ValueError("schema required in options for Avro encoding")
            
            # Encode to Avro bytes
            output = io.BytesIO()
            fastavro.schemaless_writer(output, schema, value)
            
            return output.getvalue()
            
        except Exception as e:
            raise SerializationError(
                f"Failed to encode Avro: {e}",
                format_name=self.format_name,
                original_error=e
            )
    
    def decode(self, repr: Union[bytes, str], *, options: Optional[DecodeOptions] = None) -> Any:
        """
        Decode Avro bytes to data.
        
        Uses fastavro.schemaless_reader().
        
        Args:
            repr: Avro bytes
            options: Must include 'schema' with Avro schema
        
        Returns:
            Decoded data
        
        Raises:
            SerializationError: If decoding fails
        """
        try:
            opts = options or {}
            
            # Requires schema
            schema = opts.get('schema')
            if schema is None:
                raise ValueError("schema required in options for Avro decoding")
            
            # Avro requires bytes
            if isinstance(repr, str):
                repr = repr.encode('utf-8')
            
            # Decode from Avro bytes
            input_stream = io.BytesIO(repr)
            data = fastavro.schemaless_reader(input_stream, schema)
            
            return data
            
        except Exception as e:
            raise SerializationError(
                f"Failed to decode Avro: {e}",
                format_name=self.format_name,
                original_error=e
            )


# Backward compatibility alias
AvroSerializer = XWAvroSerializer

