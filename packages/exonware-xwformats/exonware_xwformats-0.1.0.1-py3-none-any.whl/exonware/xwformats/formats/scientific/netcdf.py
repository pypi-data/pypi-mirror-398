#!/usr/bin/env python3
#exonware/xwformats/src/exonware/xwformats/formats/scientific/netcdf.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 02-Nov-2025

NetCDF Serialization - Network Common Data Form

NetCDF is a format for:
- Scientific array-oriented data
- Climate and weather data
- Geospatial information
- Self-describing metadata

Priority 1 (Security): Safe binary file handling
Priority 2 (Usability): Scientific community standard
Priority 3 (Maintainability): Clean NetCDF integration
Priority 4 (Performance): Efficient array storage
Priority 5 (Extensibility): CF conventions support
"""

from typing import Any, Optional, Union
from pathlib import Path
import netCDF4
import numpy as np

from exonware.xwsystem.io.serialization.base import ASerialization
from exonware.xwsystem.io.serialization.contracts import ISerialization
from exonware.xwsystem.io.errors import SerializationError


class XWNetcdfSerializer(ASerialization):
    """
    NetCDF (Network Common Data Form) serializer for scientific data.
    
    I: ISerialization (interface)
    A: ASerialization (abstract base)
    XW: XWNetcdfSerializer (concrete implementation)
    """
    
    def __init__(self):
        """Initialize NetCDF serializer."""
        super().__init__()
    
    @property
    def codec_id(self) -> str:
        """Codec identifier."""
        return "netcdf"
    
    @property
    def media_types(self) -> list[str]:
        """Supported MIME types."""
        return ["application/netcdf", "application/x-netcdf"]
    
    @property
    def file_extensions(self) -> list[str]:
        """Supported file extensions."""
        return [".nc", ".nc4", ".netcdf"]
    
    def encode(self, data: Any, options: Optional[dict[str, Any]] = None) -> bytes:
        """
        Encode data to NetCDF bytes.
        
        Args:
            data: dict with 'dimensions', 'variables', and optionally 'attributes'
            options: Encoding options
            
        Returns:
            NetCDF bytes
            
        Raises:
            SerializationError: If encoding fails
        """
        raise NotImplementedError(
            "NetCDF requires file-based operations. "
            "Use encode_to_file() or save to file directly."
        )
    
    def decode(self, data: bytes, options: Optional[dict[str, Any]] = None) -> Any:
        """
        Decode NetCDF bytes to Python data.
        
        Args:
            data: NetCDF bytes
            options: Decoding options
            
        Returns:
            dict with dimensions, variables, and attributes
            
        Raises:
            SerializationError: If decoding fails
        """
        raise NotImplementedError(
            "NetCDF requires file-based operations. "
            "Use decode_from_file() or load from file directly."
        )
    
    def encode_to_file(self, data: Any, file_path: Union[str, Path], options: Optional[dict[str, Any]] = None) -> None:
        """
        Encode data to NetCDF file.
        
        Args:
            data: dict with 'dimensions', 'variables', and optionally 'attributes'
            file_path: Path to output file
            options: Encoding options
        """
        opts = options or {}
        format_type = opts.get('format', 'NETCDF4')  # NETCDF3_CLASSIC, NETCDF4, etc.
        
        with netCDF4.Dataset(file_path, 'w', format=format_type) as nc:
            # Create dimensions
            if 'dimensions' in data:
                for dim_name, dim_size in data['dimensions'].items():
                    nc.createDimension(dim_name, dim_size)
            
            # Create variables
            if 'variables' in data:
                for var_name, var_data in data['variables'].items():
                    var = nc.createVariable(
                        var_name,
                        var_data.get('dtype', 'f8'),
                        var_data.get('dimensions', ())
                    )
                    var[:] = var_data.get('data', [])
                    
                    # Add variable attributes
                    if 'attributes' in var_data:
                        for attr_name, attr_value in var_data['attributes'].items():
                            setattr(var, attr_name, attr_value)
            
            # Add global attributes
            if 'attributes' in data:
                for attr_name, attr_value in data['attributes'].items():
                    setattr(nc, attr_name, attr_value)
    
    def decode_from_file(self, file_path: Union[str, Path], options: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """
        Decode NetCDF file to Python dict.
        
        Args:
            file_path: Path to NetCDF file
            options: Decoding options
            
        Returns:
            dict with dimensions, variables, and attributes
        """
        result = {
            'dimensions': {},
            'variables': {},
            'attributes': {}
        }
        
        with netCDF4.Dataset(file_path, 'r') as nc:
            # Read dimensions
            for dim_name, dim in nc.dimensions.items():
                result['dimensions'][dim_name] = len(dim)
            
            # Read variables
            for var_name, var in nc.variables.items():
                result['variables'][var_name] = {
                    'data': var[:].tolist() if hasattr(var[:], 'tolist') else var[:],
                    'dtype': str(var.dtype),
                    'dimensions': var.dimensions,
                    'attributes': {attr: getattr(var, attr) for attr in var.ncattrs()}
                }
            
            # Read global attributes
            result['attributes'] = {attr: getattr(nc, attr) for attr in nc.ncattrs()}
        
        return result


# Backward compatibility aliases
NetcdfSerializer = XWNetcdfSerializer
NetCDFSerializer = XWNetcdfSerializer

