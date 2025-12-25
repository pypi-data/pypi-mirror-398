"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: November 2, 2025

ORC serialization - Apache ORC columnar storage.

Following I→A→XW pattern:
- I: ISerialization (interface)
- A: ASerialization (abstract base)
- XW: XWOrcSerializer (concrete implementation)
"""

import io
from typing import Any, Optional, Union
from pathlib import Path

from exonware.xwsystem.io.serialization.base import ASerialization
from exonware.xwsystem.io.contracts import EncodeOptions, DecodeOptions
from exonware.xwsystem.io.defs import CodecCapability
from exonware.xwsystem.io.errors import SerializationError
import pyorc


class XWOrcSerializer(ASerialization):
    """
    ORC serializer - follows I→A→XW pattern.
    
    Uses pyorc library for Apache ORC format.
    """
    
    def __init__(self):
        """Initialize ORC serializer."""
        super().__init__()
    
    @property
    def codec_id(self) -> str:
        return "orc"
    
    @property
    def media_types(self) -> list[str]:
        return ["application/orc"]
    
    @property
    def file_extensions(self) -> list[str]:
        return [".orc"]
    
    @property
    def format_name(self) -> str:
        return "ORC"
    
    @property
    def mime_type(self) -> str:
        return "application/orc"
    
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
        return ["orc", "ORC"]
    
    def encode(self, value: Any, *, options: Optional[EncodeOptions] = None) -> Union[bytes, str]:
        """Encode data to ORC bytes."""
        try:
            opts = options or {}
            schema = opts.get('schema')
            if schema is None:
                raise ValueError("schema required for ORC encoding")
            
            output = io.BytesIO()
            with pyorc.Writer(output, schema) as writer:
                if isinstance(value, list):
                    for row in value:
                        writer.write(row)
                else:
                    writer.write(value)
            
            return output.getvalue()
        except Exception as e:
            raise SerializationError(f"Failed to encode ORC: {e}", self.format_name, e)
    
    def decode(self, repr: Union[bytes, str], *, options: Optional[DecodeOptions] = None) -> Any:
        """Decode ORC bytes to data."""
        try:
            if isinstance(repr, str):
                repr = repr.encode('utf-8')
            
            input_stream = io.BytesIO(repr)
            reader = pyorc.Reader(input_stream)
            return list(reader)
        except Exception as e:
            raise SerializationError(f"Failed to decode ORC: {e}", self.format_name, e)


OrcSerializer = XWOrcSerializer

