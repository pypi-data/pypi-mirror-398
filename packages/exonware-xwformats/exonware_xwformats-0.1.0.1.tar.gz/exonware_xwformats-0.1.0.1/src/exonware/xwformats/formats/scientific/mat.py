#!/usr/bin/env python3
#exonware/xwformats/src/exonware/xwformats/formats/scientific/mat.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 02-Nov-2025

MATLAB MAT File Serialization

MAT files are MATLAB's binary data format for:
- Numerical arrays
- Structures and cells
- MATLAB workspace variables
- Scientific computing interop

Priority 1 (Security): Safe MAT file loading
Priority 2 (Usability): MATLAB interoperability
Priority 3 (Maintainability): Clean scipy integration
Priority 4 (Performance): Efficient array storage
Priority 5 (Extensibility): Compatible with MATLAB ecosystem
"""

from typing import Any, Optional, Union
from pathlib import Path
import scipy.io

from exonware.xwsystem.io.serialization.base import ASerialization
from exonware.xwsystem.io.serialization.contracts import ISerialization


class XWMatSerializer(ASerialization):
    """
    MATLAB MAT file serializer for scientific data interchange.
    
    I: ISerialization (interface)
    A: ASerialization (abstract base)
    XW: XWMatSerializer (concrete implementation)
    """
    
    def __init__(self):
        """Initialize MAT serializer."""
        super().__init__()
    
    @property
    def codec_id(self) -> str:
        """Codec identifier."""
        return "mat"
    
    @property
    def media_types(self) -> list[str]:
        """Supported MIME types."""
        return ["application/x-matlab-data", "application/matlab"]
    
    @property
    def file_extensions(self) -> list[str]:
        """Supported file extensions."""
        return [".mat"]
    
    def encode(self, data: Any, options: Optional[dict[str, Any]] = None) -> bytes:
        """
        Encode data to MAT bytes.
        
        Note: MAT files are best saved directly to disk.
        This method uses a temporary approach.
        
        Args:
            data: Dictionary of variables
            options: Encoding options
            
        Returns:
            MAT file bytes
        """
        import io
        from scipy.io import savemat
        
        if not isinstance(data, dict):
            data = {'data': data}
        
        # Use BytesIO to create in-memory MAT file
        buffer = io.BytesIO()
        
        # savemat doesn't support BytesIO directly, so we need temp file
        raise NotImplementedError(
            "MAT encoding to bytes not supported. "
            "Use encode_to_file() or save to file directly."
        )
    
    def decode(self, data: bytes, options: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """
        Decode MAT bytes to Python data.
        
        Args:
            data: MAT file bytes
            options: Decoding options
            
        Returns:
            Dictionary of MATLAB variables
        """
        import io
        from scipy.io import loadmat
        
        buffer = io.BytesIO(data)
        return loadmat(buffer)
    
    def encode_to_file(self, data: Any, file_path: Union[str, Path], options: Optional[dict[str, Any]] = None) -> None:
        """
        Encode data to MAT file.
        
        Args:
            data: Dictionary of MATLAB variables
            file_path: Path to output .mat file
            options: Encoding options (do_compression, etc.)
        """
        if not isinstance(data, dict):
            data = {'data': data}
        
        opts = options or {}
        do_compression = opts.get('do_compression', False)
        
        scipy.io.savemat(
            str(file_path),
            data,
            do_compression=do_compression
        )
    
    def decode_from_file(self, file_path: Union[str, Path], options: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """
        Decode MAT file to Python dict.
        
        Args:
            file_path: Path to .mat file
            options: Decoding options
            
        Returns:
            Dictionary of MATLAB variables
        """
        # Load MAT file
        mat_data = scipy.io.loadmat(str(file_path))
        
        # Remove MATLAB metadata keys
        result = {k: v for k, v in mat_data.items() if not k.startswith('__')}
        
        return result


# Backward compatibility aliases
MatSerializer = XWMatSerializer
MatlabSerializer = XWMatSerializer

