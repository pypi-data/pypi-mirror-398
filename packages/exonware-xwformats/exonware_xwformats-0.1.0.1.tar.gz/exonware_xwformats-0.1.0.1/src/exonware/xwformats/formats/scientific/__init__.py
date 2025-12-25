#!/usr/bin/env python3
#exonware/xwformats/src/exonware/xwformats/formats/scientific/__init__.py
"""
Scientific data serialization formats.

Note: Import these modules explicitly due to large dependencies (scipy, h5py, etc.)
These are not auto-imported to avoid loading heavy scientific packages.
"""

# Standard imports following DEV_GUIDELINES - no try/except
# Users with [full] extra have them pre-installed
from .hdf5 import XWHdf5Serializer, Hdf5Serializer
from .feather import XWFeatherSerializer, FeatherSerializer
from .zarr import XWZarrSerializer, ZarrSerializer
from .netcdf import XWNetcdfSerializer, NetcdfSerializer, NetCDFSerializer
from .mat import XWMatSerializer, MatSerializer, MatlabSerializer

__all__ = [
    # I→A→XW pattern (XW prefix)
    "XWHdf5Serializer",
    "XWFeatherSerializer",
    "XWZarrSerializer",
    "XWNetcdfSerializer",
    "XWMatSerializer",
    
    # Backward compatibility aliases
    "Hdf5Serializer",
    "FeatherSerializer",
    "ZarrSerializer",
    "NetcdfSerializer",
    "NetCDFSerializer",
    "MatSerializer",
    "MatlabSerializer",
]
