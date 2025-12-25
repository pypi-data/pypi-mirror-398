"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: November 2, 2025

Feather serialization - Fast DataFrame storage.

Following I→A→XW pattern:
- I: ISerialization (interface)
- A: ASerialization (abstract base)
- XW: XWFeatherSerializer (concrete implementation)
"""

import io
from typing import Any, Optional, Union
from pathlib import Path

from exonware.xwsystem.io.serialization.base import ASerialization
from exonware.xwsystem.io.contracts import EncodeOptions, DecodeOptions
from exonware.xwsystem.io.defs import CodecCapability
from exonware.xwsystem.io.errors import SerializationError
import pyarrow as pa
import pyarrow.feather as feather


class XWFeatherSerializer(ASerialization):
    """
    Feather serializer - follows I→A→XW pattern.
    
    Uses pyarrow.feather for DataFrame storage.
    """
    
    def __init__(self):
        """Initialize Feather serializer."""
        super().__init__()
    
    @property
    def codec_id(self) -> str:
        return "feather"
    
    @property
    def media_types(self) -> list[str]:
        return ["application/feather", "application/vnd.apache.arrow.file"]
    
    @property
    def file_extensions(self) -> list[str]:
        return [".feather", ".arrow"]
    
    @property
    def format_name(self) -> str:
        return "Feather"
    
    @property
    def mime_type(self) -> str:
        return "application/feather"
    
    @property
    def is_binary_format(self) -> bool:
        return True
    
    @property
    def supports_streaming(self) -> bool:
        return False
    
    @property
    def capabilities(self) -> CodecCapability:
        return CodecCapability.BIDIRECTIONAL
    
    @property
    def aliases(self) -> list[str]:
        return ["feather", "arrow"]
    
    def encode(self, value: Any, *, options: Optional[EncodeOptions] = None) -> Union[bytes, str]:
        """Encode DataFrame to Feather bytes."""
        try:
            # Convert to Arrow table
            if isinstance(value, pa.Table):
                table = value
            elif hasattr(value, 'to_arrow'):  # pandas DataFrame
                table = pa.Table.from_pandas(value)
            else:
                raise TypeError(f"Unsupported type for Feather: {type(value)}")
            
            # Write to bytes
            output = io.BytesIO()
            feather.write_feather(table, output)
            return output.getvalue()
        except Exception as e:
            raise SerializationError(f"Failed to encode Feather: {e}", self.format_name, e)
    
    def decode(self, repr: Union[bytes, str], *, options: Optional[DecodeOptions] = None) -> Any:
        """Decode Feather bytes to DataFrame."""
        try:
            if isinstance(repr, str):
                repr = repr.encode('utf-8')
            
            input_stream = io.BytesIO(repr)
            table = feather.read_feather(input_stream)
            
            opts = options or {}
            if opts.get('as_dataframe', True):
                return table.to_pandas()
            return table
        except Exception as e:
            raise SerializationError(f"Failed to decode Feather: {e}", self.format_name, e)


FeatherSerializer = XWFeatherSerializer

