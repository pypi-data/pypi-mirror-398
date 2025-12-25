"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: November 2, 2025

Parquet serialization - Apache Parquet columnar storage format.

Following I→A→XW pattern:
- I: ISerialization (interface)
- A: ASerialization (abstract base)
- XW: XWParquetSerializer (concrete implementation)
"""

import io
from typing import Any, Optional, Union
from pathlib import Path

from exonware.xwsystem.io.serialization.base import ASerialization
from exonware.xwsystem.io.contracts import EncodeOptions, DecodeOptions
from exonware.xwsystem.io.defs import CodecCapability
from exonware.xwsystem.io.errors import SerializationError

import pyarrow as pa
import pyarrow.parquet as pq


class XWParquetSerializer(ASerialization):
    """
    Parquet serializer - follows I→A→XW pattern.
    
    I: ISerialization (interface)
    A: ASerialization (abstract base)
    XW: XWParquetSerializer (concrete implementation)
    
    Uses pyarrow library for Apache Parquet format.
    
    Examples:
        >>> serializer = XWParquetSerializer()
        >>> 
        >>> # Encode data (list of dicts or pandas DataFrame)
        >>> parquet_bytes = serializer.encode(data)
        >>> 
        >>> # Decode to list of dicts
        >>> data = serializer.decode(parquet_bytes)
    """
    
    def __init__(self):
        """Initialize Parquet serializer."""
        super().__init__()
    
    # ========================================================================
    # CODEC METADATA
    # ========================================================================
    
    @property
    def codec_id(self) -> str:
        return "parquet"
    
    @property
    def media_types(self) -> list[str]:
        return ["application/parquet", "application/x-parquet"]
    
    @property
    def file_extensions(self) -> list[str]:
        return [".parquet", ".parq"]
    
    @property
    def format_name(self) -> str:
        return "Parquet"
    
    @property
    def mime_type(self) -> str:
        return "application/parquet"
    
    @property
    def is_binary_format(self) -> bool:
        return True  # Parquet is binary
    
    @property
    def supports_streaming(self) -> bool:
        return True  # Parquet supports streaming
    
    @property
    def capabilities(self) -> CodecCapability:
        return CodecCapability.BIDIRECTIONAL | CodecCapability.SCHEMA
    
    @property
    def aliases(self) -> list[str]:
        return ["parquet", "PARQUET", "parq"]
    
    @property
    def codec_types(self) -> list[str]:
        """Parquet is a binary schema format for columnar data."""
        return ["binary", "schema", "data"]
    
    # ========================================================================
    # CORE ENCODE/DECODE (Using pyarrow)
    # ========================================================================
    
    def encode(self, value: Any, *, options: Optional[EncodeOptions] = None) -> Union[bytes, str]:
        """
        Encode data to Parquet bytes.
        
        Uses pyarrow.parquet.
        
        Args:
            value: Data to serialize (list of dicts, pandas DataFrame, or pyarrow Table)
            options: Parquet options (compression, etc.)
        
        Returns:
            Parquet bytes
        
        Raises:
            SerializationError: If encoding fails
        """
        try:
            opts = options or {}
            
            # Convert to pyarrow Table
            if isinstance(value, list):
                table = pa.Table.from_pylist(value)
            elif hasattr(value, 'to_arrow'):  # pandas DataFrame
                table = value.to_arrow()
            elif isinstance(value, pa.Table):
                table = value
            else:
                raise TypeError(f"Unsupported type for Parquet: {type(value)}")
            
            # Write to bytes
            output = io.BytesIO()
            pq.write_table(
                table,
                output,
                compression=opts.get('compression', 'snappy'),
                use_dictionary=opts.get('use_dictionary', True),
                write_statistics=opts.get('write_statistics', True)
            )
            
            return output.getvalue()
            
        except Exception as e:
            raise SerializationError(
                f"Failed to encode Parquet: {e}",
                format_name=self.format_name,
                original_error=e
            )
    
    def decode(self, repr: Union[bytes, str], *, options: Optional[DecodeOptions] = None) -> Any:
        """
        Decode Parquet bytes to data.
        
        Uses pyarrow.parquet.
        
        Args:
            repr: Parquet bytes
            options: Decoding options (columns, use_pandas_metadata, etc.)
        
        Returns:
            List of dicts or pandas DataFrame
        
        Raises:
            SerializationError: If decoding fails
        """
        try:
            # Parquet requires bytes
            if isinstance(repr, str):
                repr = repr.encode('utf-8')
            
            opts = options or {}
            
            # Read from bytes
            input_stream = io.BytesIO(repr)
            table = pq.read_table(
                input_stream,
                columns=opts.get('columns', None),
                use_pandas_metadata=opts.get('use_pandas_metadata', False)
            )
            
            # Convert to list of dicts (or DataFrame if requested)
            if opts.get('as_dataframe', False):
                return table.to_pandas()
            else:
                return table.to_pylist()
            
        except Exception as e:
            raise SerializationError(
                f"Failed to decode Parquet: {e}",
                format_name=self.format_name,
                original_error=e
            )


# Backward compatibility alias
ParquetSerializer = XWParquetSerializer

