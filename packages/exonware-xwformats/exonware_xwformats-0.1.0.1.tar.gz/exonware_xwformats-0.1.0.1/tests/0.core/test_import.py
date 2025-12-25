#!/usr/bin/env python3
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1
Generation Date: 04-Nov-2025

Test xwformats import and basic functionality.
"""

import pytest


def test_import_xwformats():
    """Test that xwformats can be imported."""
    import exonware.xwformats
    assert exonware.xwformats is not None


def test_version_info():
    """Test that version information is available."""
    from exonware.xwformats import __version__, __author__, __email__, __company__
    
    assert __version__ == "0.0.1.5"  # Updated to match actual version
    assert __author__ == "Eng. Muhammad AlShehri"
    assert __email__ == "connect@exonware.com"
    assert __company__ == "eXonware.com"


def test_import_schema_formats():
    """Test that schema formats can be imported."""
    from exonware.xwformats.formats.schema import (
        XWProtobufSerializer, ProtobufSerializer,
        XWParquetSerializer, ParquetSerializer,
        XWThriftSerializer, ThriftSerializer,
        XWOrcSerializer, OrcSerializer,
        XWCapnProtoSerializer, CapnProtoSerializer,
        XWFlatBuffersSerializer, FlatBuffersSerializer,
    )
    
    # Check aliases work
    assert ProtobufSerializer is XWProtobufSerializer
    assert ParquetSerializer is XWParquetSerializer


def test_import_scientific_formats():
    """Test that scientific formats can be imported."""
    from exonware.xwformats.formats.scientific import (
        XWHdf5Serializer, Hdf5Serializer,
        XWFeatherSerializer, FeatherSerializer,
        XWZarrSerializer, ZarrSerializer,
        XWNetcdfSerializer, NetcdfSerializer,
        XWMatSerializer, MatSerializer,
    )
    
    # Check aliases work
    assert Hdf5Serializer is XWHdf5Serializer
    assert FeatherSerializer is XWFeatherSerializer


def test_import_database_formats():
    """Test that database formats can be imported."""
    from exonware.xwformats.formats.database import (
        XWLmdbSerializer, LmdbSerializer,
        XWGraphDbSerializer, GraphDbSerializer,
        XWLeveldbSerializer, LeveldbSerializer,
    )
    
    # Check aliases work
    assert LmdbSerializer is XWLmdbSerializer
    assert GraphDbSerializer is XWGraphDbSerializer
    assert LeveldbSerializer is XWLeveldbSerializer


def test_import_binary_formats():
    """Test that binary formats can be imported."""
    from exonware.xwformats.formats.binary import (
        XWUbjsonSerializer, UbjsonSerializer,
    )
    
    # Check aliases work
    assert UbjsonSerializer is XWUbjsonSerializer


def test_avro_import_handling():
    """Test that Avro import is handled gracefully if unavailable."""
    try:
        from exonware.xwformats.formats.schema import XWAvroSerializer, AvroSerializer
        # If we get here, Avro is available
        assert AvroSerializer is XWAvroSerializer
    except (ImportError, NameError):
        # Avro not available (expected on some platforms)
        pass


def test_codec_registry_integration():
    """Test that xwformats integrates with UniversalCodecRegistry."""
    from exonware.xwsystem.io.codec.registry import get_registry
    
    registry = get_registry()
    codecs = registry.list_codecs()
    
    # Check that enterprise formats are registered
    expected_codecs = [
        'protobuf', 'parquet', 'thrift', 'orc', 'capnproto', 'flatbuffers',
        'hdf5', 'feather', 'netcdf',
        'lmdb', 'graphdb',
        'ubjson',
    ]
    
    for codec_id in expected_codecs:
        assert codec_id in codecs, f"Codec {codec_id} not found in registry"


def test_get_codec_by_id():
    """Test that we can get codecs by ID from registry."""
    from exonware.xwsystem.io.codec.registry import get_registry
    
    registry = get_registry()
    
    # Test getting a few codecs
    protobuf_codec = registry.get_codec('protobuf')
    assert protobuf_codec is not None
    assert protobuf_codec.format_name == "Protobuf"
    
    parquet_codec = registry.get_codec('parquet')
    assert parquet_codec is not None
    assert parquet_codec.format_name == "Parquet"
    
    hdf5_codec = registry.get_codec('hdf5')
    assert hdf5_codec is not None
    assert hdf5_codec.format_name == "HDF5"


def test_serializer_instantiation():
    """Test that serializers can be instantiated."""
    from exonware.xwformats import (
        XWProtobufSerializer,
        XWParquetSerializer,
        XWHdf5Serializer,
        XWUbjsonSerializer,
    )
    
    # Test instantiation (some may require dependencies)
    try:
        protobuf = XWProtobufSerializer()
        assert protobuf.codec_id == "protobuf"
    except ImportError:
        pass  # protobuf not installed
    
    try:
        parquet = XWParquetSerializer()
        assert parquet.codec_id == "parquet"
    except ImportError:
        pass  # pyarrow not installed
    
    try:
        hdf5 = XWHdf5Serializer()
        assert hdf5.codec_id == "hdf5"
    except ImportError:
        pass  # h5py not installed
    
    try:
        ubjson = XWUbjsonSerializer()
        assert ubjson.codec_id == "ubjson"
    except ImportError:
        pass  # ubjson not installed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


