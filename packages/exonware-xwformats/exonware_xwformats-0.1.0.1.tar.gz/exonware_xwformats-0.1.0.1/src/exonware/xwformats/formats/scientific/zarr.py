"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: November 2, 2025

Zarr serialization - Chunked, compressed N-dimensional arrays.

Following I→A→XW pattern:
- I: ISerialization (interface)
- A: ASerialization (abstract base)
- XW: XWZarrSerializer (concrete implementation)
"""

from typing import Any, Optional, Union
from pathlib import Path

from exonware.xwsystem.io.serialization.base import ASerialization
from exonware.xwsystem.io.contracts import EncodeOptions, DecodeOptions
from exonware.xwsystem.io.defs import CodecCapability
from exonware.xwsystem.io.errors import SerializationError
import zarr


class XWZarrSerializer(ASerialization):
    """
    Zarr serializer - follows I→A→XW pattern.
    
    Uses zarr library for array storage.
    """
    
    def __init__(self):
        """Initialize Zarr serializer."""
        super().__init__()
    
    @property
    def codec_id(self) -> str:
        return "zarr"
    
    @property
    def media_types(self) -> list[str]:
        return ["application/zarr"]
    
    @property
    def file_extensions(self) -> list[str]:
        return [".zarr"]
    
    @property
    def format_name(self) -> str:
        return "Zarr"
    
    @property
    def mime_type(self) -> str:
        return "application/zarr"
    
    @property
    def is_binary_format(self) -> bool:
        return True
    
    @property
    def supports_streaming(self) -> bool:
        return True
    
    @property
    def capabilities(self) -> CodecCapability:
        return CodecCapability.BIDIRECTIONAL
    
    @property
    def aliases(self) -> list[str]:
        return ["zarr", "ZARR"]
    
    def encode(self, value: Any, *, options: Optional[EncodeOptions] = None) -> Union[bytes, str]:
        """Encode array to Zarr bytes (requires file path - use save_file())."""
        raise NotImplementedError("Zarr encode to memory not supported - use save_file() instead")
    
    def decode(self, repr: Union[bytes, str], *, options: Optional[DecodeOptions] = None) -> Any:
        """Decode Zarr bytes to array (requires file path - use load_file())."""
        raise NotImplementedError("Zarr decode from memory not supported - use load_file() instead")


ZarrSerializer = XWZarrSerializer

