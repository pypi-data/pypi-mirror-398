#!/usr/bin/env python3
#exonware/xwformats/src/exonware/xwformats/formats/binary/__init__.py
"""Enterprise binary serialization formats."""

from .ubjson import XWUbjsonSerializer, UbjsonSerializer

try:
    from .bson import XWBsonSerializer
    BSON_AVAILABLE = True
except ImportError:
    BSON_AVAILABLE = False
    XWBsonSerializer = None

__all__ = [
    "XWUbjsonSerializer",
    "UbjsonSerializer",
]

if BSON_AVAILABLE:
    __all__.append("XWBsonSerializer")

