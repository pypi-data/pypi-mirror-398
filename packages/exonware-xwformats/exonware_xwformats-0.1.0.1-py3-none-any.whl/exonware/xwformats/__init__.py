#!/usr/bin/env python3
#exonware/xwformats/src/exonware/xwformats/__init__.py
"""
xwformats: Enterprise Serialization Formats

Extended serialization format support for enterprise applications.
This library provides heavyweight formats that are typically used in
specialized domains (scientific computing, big data, enterprise systems).

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 02-Nov-2025

Formats provided:
- Schema: Protobuf, Avro, Parquet, Thrift, ORC, Cap'n Proto, FlatBuffers (7)
- Scientific: HDF5, Feather, Zarr, NetCDF, MAT (5)
- Database: LMDB, GraphDB, LevelDB (3)
- Binary: BSON, UBJSON (2)
- Text: CSV, YAML, TOML, XML (4)

Total: 21 enterprise formats (~87 MB dependencies)

Installation:
    # Install with all dependencies
    pip install exonware-xwformats[full]
    
    # Or minimal install (dependencies required separately)
    pip install exonware-xwformats
"""

from .version import __version__

# Version metadata constants
__author__ = "Eng. Muhammad AlShehri"
__email__ = "connect@exonware.com"
__company__ = "eXonware.com"

# LAZY INSTALLATION - Simple One-Line Configuration
# Auto-detects [lazy] extra and enables lazy installation hook
from exonware.xwsystem.utils.lazy_discovery import config_package_lazy_install_enabled
config_package_lazy_install_enabled("xwformats")  # Auto-detect [lazy] extra

# Import all format serializers
from .formats import *

# Auto-register all serializers with UniversalCodecRegistry
from exonware.xwsystem.io.codec.registry import get_registry

_codec_registry = get_registry()

# Get all serializer classes from formats
from .formats.schema import (
    XWProtobufSerializer, XWParquetSerializer, XWThriftSerializer,
    XWOrcSerializer, XWCapnProtoSerializer, XWFlatBuffersSerializer,
)
# Note: Avro excluded due to cramjam bug on Python 3.12 Windows - see KNOWN_ISSUES.md
from .formats.scientific import (
    XWHdf5Serializer, XWFeatherSerializer, XWZarrSerializer,
    XWNetcdfSerializer, XWMatSerializer,
)
from .formats.database import (
    XWLmdbSerializer, XWGraphDbSerializer, XWLeveldbSerializer,
)
from .formats.binary import (
    XWUbjsonSerializer,
)
try:
    from .formats.binary import XWBsonSerializer
    BSON_AVAILABLE = True
except ImportError:
    BSON_AVAILABLE = False
    XWBsonSerializer = None

try:
    from .formats.text import (
        XWCsvSerializer,
        XWYamlSerializer,
        XWTomlSerializer,
        XWXmlSerializer,
    )
    TEXT_FORMATS_AVAILABLE = True
except ImportError:
    TEXT_FORMATS_AVAILABLE = False
    XWCsvSerializer = None
    XWYamlSerializer = None
    XWTomlSerializer = None
    XWXmlSerializer = None

# Register all serializers
_serializers_to_register = [
    # Schema formats (Avro excluded - see KNOWN_ISSUES.md)
    XWProtobufSerializer, XWParquetSerializer, XWThriftSerializer,
    XWOrcSerializer, XWCapnProtoSerializer, XWFlatBuffersSerializer,
    # Scientific formats
    XWHdf5Serializer, XWFeatherSerializer, XWZarrSerializer,
    XWNetcdfSerializer, XWMatSerializer,
    # Database formats
    XWLmdbSerializer, XWGraphDbSerializer, XWLeveldbSerializer,
    # Binary formats
    XWUbjsonSerializer,
]

# Add text formats if available
if TEXT_FORMATS_AVAILABLE:
    if XWCsvSerializer:
        _serializers_to_register.append(XWCsvSerializer)
    if XWYamlSerializer:
        _serializers_to_register.append(XWYamlSerializer)
    if XWTomlSerializer:
        _serializers_to_register.append(XWTomlSerializer)
    if XWXmlSerializer:
        _serializers_to_register.append(XWXmlSerializer)

# Add BSON if available
if BSON_AVAILABLE and XWBsonSerializer:
    _serializers_to_register.append(XWBsonSerializer)

# Add text formats if available
if TEXT_FORMATS_AVAILABLE:
    if XWCsvSerializer:
        _serializers_to_register.append(XWCsvSerializer)
    if XWYamlSerializer:
        _serializers_to_register.append(XWYamlSerializer)
    if XWTomlSerializer:
        _serializers_to_register.append(XWTomlSerializer)
    if XWXmlSerializer:
        _serializers_to_register.append(XWXmlSerializer)

# Register all serializers
for _serializer_class in _serializers_to_register:
    if _serializer_class is not None:
        try:
            _codec_registry.register(_serializer_class)
        except Exception:
            # Skip registration if serializer has missing dependencies
            pass

__all__ = [
    # Version info
    '__version__',
    '__author__',
    '__email__',
    '__company__',
    
    # All formats exported from formats module
    # (will be populated by formats/__init__.py)
]

