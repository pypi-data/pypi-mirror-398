#!/usr/bin/env python3
#exonware/xwformats/src/exonware/xwformats/formats/schema/__init__.py
"""Schema-based enterprise serialization formats.

Note: Avro import is separate due to known cramjam bug on Python 3.12 Windows.
This is an external dependency issue, not a bug in xwformats.
See KNOWN_ISSUES.md for details.
"""

from .protobuf import XWProtobufSerializer, ProtobufSerializer
from .parquet import XWParquetSerializer, ParquetSerializer
from .thrift import XWThriftSerializer, ThriftSerializer
from .orc import XWOrcSerializer, OrcSerializer
from .capnproto import XWCapnProtoSerializer, CapnProtoSerializer
from .flatbuffers import XWFlatBuffersSerializer, FlatBuffersSerializer

__all__ = [
    # I→A→XW pattern (XW prefix)
    "XWProtobufSerializer",
    "XWParquetSerializer",
    "XWThriftSerializer",
    "XWOrcSerializer",
    "XWCapnProtoSerializer",
    "XWFlatBuffersSerializer",
    
    # Backward compatibility aliases
    "ProtobufSerializer",
    "ParquetSerializer",
    "ThriftSerializer",
    "OrcSerializer",
    "CapnProtoSerializer",
    "FlatBuffersSerializer",
]

# Avro: Excluded from default import due to cramjam bug on Python 3.12 Windows
# This is an EXTERNAL dependency bug, not a xwformats issue
# See KNOWN_ISSUES.md for details and workarounds
# When cramjam fixes the bug, uncomment these lines:
# from .avro import XWAvroSerializer, AvroSerializer
# __all__.extend(["XWAvroSerializer", "AvroSerializer"])
