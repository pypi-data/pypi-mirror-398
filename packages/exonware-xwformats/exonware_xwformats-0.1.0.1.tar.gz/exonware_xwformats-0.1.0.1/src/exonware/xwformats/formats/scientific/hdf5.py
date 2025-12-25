"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: November 2, 2025

HDF5 serialization - Hierarchical Data Format.

Following I→A→XW pattern:
- I: ISerialization (interface)
- A: ASerialization (abstract base)
- XW: XWHdf5Serializer (concrete implementation)
"""

import io
from typing import Any, Optional, Union
from pathlib import Path

from exonware.xwsystem.io.serialization.base import ASerialization
from exonware.xwsystem.io.contracts import EncodeOptions, DecodeOptions
from exonware.xwsystem.io.defs import CodecCapability
from exonware.xwsystem.io.errors import SerializationError
import h5py


class XWHdf5Serializer(ASerialization):
    """
    HDF5 serializer - follows I→A→XW pattern.
    
    Uses h5py library for hierarchical data storage.
    """
    
    def __init__(self):
        """Initialize HDF5 serializer."""
        super().__init__()
    
    @property
    def codec_id(self) -> str:
        return "hdf5"
    
    @property
    def media_types(self) -> list[str]:
        return ["application/x-hdf", "application/x-hdf5"]
    
    @property
    def file_extensions(self) -> list[str]:
        return [".h5", ".hdf5", ".he5"]
    
    @property
    def format_name(self) -> str:
        return "HDF5"
    
    @property
    def mime_type(self) -> str:
        return "application/x-hdf5"
    
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
        return ["hdf5", "HDF5", "h5"]
    
    def encode(self, value: Any, *, options: Optional[EncodeOptions] = None) -> Union[bytes, str]:
        """Encode data to HDF5 bytes (requires file path in options)."""
        raise NotImplementedError("HDF5 encode to memory not supported - use save_file() instead")
    
    def decode(self, repr: Union[bytes, str], *, options: Optional[DecodeOptions] = None) -> Any:
        """Decode HDF5 bytes to data (requires file path in options)."""
        raise NotImplementedError("HDF5 decode from memory not supported - use load_file() instead")


Hdf5Serializer = XWHdf5Serializer

