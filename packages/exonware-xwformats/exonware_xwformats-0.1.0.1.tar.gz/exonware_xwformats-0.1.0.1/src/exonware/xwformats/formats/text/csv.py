#!/usr/bin/env python3
#exonware/xwformats/src/exonware/xwformats/formats/text/csv.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 15-Nov-2025

CSV Serialization - Comma-Separated Values

CSV is a simple text format for tabular data:
- Widely used for data exchange
- Human-readable
- Simple structure
- Supports headers and custom delimiters

Priority 1 (Security): Safe CSV parsing (prevent injection)
Priority 2 (Usability): Simple CSV read/write API
Priority 3 (Maintainability): Clean CSV handling
Priority 4 (Performance): Efficient CSV parsing
Priority 5 (Extensibility): Support various CSV dialects
"""

from typing import Any, Optional, Union, List, Dict
from pathlib import Path
import csv
import io

from exonware.xwsystem.io.serialization.base import ASerialization
from exonware.xwsystem.io.serialization.contracts import ISerialization
from exonware.xwsystem.io.contracts import EncodeOptions, DecodeOptions
from exonware.xwsystem.io.errors import SerializationError


class XWCsvSerializer(ASerialization):
    """
    CSV (Comma-Separated Values) serializer.
    
    I: ISerialization (interface)
    A: ASerialization (abstract base)
    XW: XWCsvSerializer (concrete implementation)
    """
    
    def __init__(self):
        """Initialize CSV serializer."""
        super().__init__()
    
    @property
    def codec_id(self) -> str:
        """Codec identifier."""
        return "csv"
    
    @property
    def media_types(self) -> list[str]:
        """Supported media types."""
        return ["text/csv", "application/csv"]
    
    @property
    def file_extensions(self) -> list[str]:
        """Supported file extensions."""
        return [".csv"]
    
    @property
    def format_name(self) -> str:
        """Format name."""
        return "CSV"
    
    @property
    def mime_type(self) -> str:
        """MIME type."""
        return "text/csv"
    
    @property
    def is_binary_format(self) -> bool:
        """Whether format is binary."""
        return False
    
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
        Encode data to CSV.
        
        Args:
            data: Data to encode (list of dicts or list of lists)
            options: Encoding options (delimiter, quotechar, etc.)
            
        Returns:
            CSV-encoded bytes
            
        Raises:
            SerializationError: If encoding fails
        """
        options = options or {}
        delimiter = options.get('delimiter', ',')
        quotechar = options.get('quotechar', '"')
        quoting = options.get('quoting', csv.QUOTE_MINIMAL)
        lineterminator = options.get('lineterminator', '\n')
        header = options.get('header', True)
        
        try:
            output = io.StringIO()
            
            # Convert data to list of dicts or list of lists
            if isinstance(data, list) and len(data) > 0:
                if isinstance(data[0], dict):
                    # List of dicts - use DictWriter
                    fieldnames = list(data[0].keys())
                    writer = csv.DictWriter(
                        output,
                        fieldnames=fieldnames,
                        delimiter=delimiter,
                        quotechar=quotechar,
                        quoting=quoting,
                        lineterminator=lineterminator
                    )
                    if header:
                        writer.writeheader()
                    writer.writerows(data)
                else:
                    # List of lists - use writer
                    writer = csv.writer(
                        output,
                        delimiter=delimiter,
                        quotechar=quotechar,
                        quoting=quoting,
                        lineterminator=lineterminator
                    )
                    writer.writerows(data)
            elif isinstance(data, dict):
                # Single dict - convert to list
                writer = csv.DictWriter(
                    output,
                    fieldnames=list(data.keys()),
                    delimiter=delimiter,
                    quotechar=quotechar,
                    quoting=quoting,
                    lineterminator=lineterminator
                )
                if header:
                    writer.writeheader()
                writer.writerow(data)
            else:
                raise ValueError(f"Unsupported data type for CSV: {type(data)}")
            
            return output.getvalue().encode('utf-8')
        except Exception as e:
            raise SerializationError(f"CSV encoding failed: {e}") from e
    
    def decode(
        self,
        data: Union[bytes, bytearray, str],
        options: Optional[DecodeOptions] = None
    ) -> Any:
        """
        Decode CSV data.
        
        Args:
            data: CSV-encoded bytes or string
            options: Decoding options (delimiter, header, etc.)
            
        Returns:
            Decoded data (list of dicts if header=True, list of lists otherwise)
            
        Raises:
            SerializationError: If decoding fails
        """
        options = options or {}
        delimiter = options.get('delimiter', ',')
        quotechar = options.get('quotechar', '"')
        header = options.get('header', True)
        
        try:
            if isinstance(data, (bytes, bytearray)):
                data = data.decode('utf-8')
            
            input_stream = io.StringIO(data)
            
            if header:
                # Use DictReader for dict output
                reader = csv.DictReader(
                    input_stream,
                    delimiter=delimiter,
                    quotechar=quotechar
                )
                return list(reader)
            else:
                # Use reader for list output
                reader = csv.reader(
                    input_stream,
                    delimiter=delimiter,
                    quotechar=quotechar
                )
                return list(reader)
        except Exception as e:
            raise SerializationError(f"CSV decoding failed: {e}") from e
    
    def encode_to_file(
        self,
        data: Any,
        file_path: Union[str, Path],
        options: Optional[EncodeOptions] = None
    ) -> None:
        """
        Encode data to CSV file.
        
        Args:
            data: Data to encode
            file_path: Path to output file
            options: Encoding options
        """
        csv_data = self.encode(data, options)
        file_path = Path(file_path)
        file_path.write_bytes(csv_data)
    
    def decode_from_file(
        self,
        file_path: Union[str, Path],
        options: Optional[DecodeOptions] = None
    ) -> Any:
        """
        Decode CSV from file.
        
        Args:
            file_path: Path to CSV file
            options: Decoding options
            
        Returns:
            Decoded data
        """
        file_path = Path(file_path)
        csv_data = file_path.read_bytes()
        return self.decode(csv_data, options)

