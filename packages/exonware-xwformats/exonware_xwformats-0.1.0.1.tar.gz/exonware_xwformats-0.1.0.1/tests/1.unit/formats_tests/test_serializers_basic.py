#!/usr/bin/env python3
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1
Generation Date: 04-Nov-2025

Basic unit tests for xwformats serializers.
"""

import pytest


class TestSerializerMetadata:
    """Test serializer metadata (codec_id, format_name, etc.)."""
    
    def test_protobuf_metadata(self):
        """Test Protobuf serializer metadata."""
        try:
            from exonware.xwformats import XWProtobufSerializer
            serializer = XWProtobufSerializer()
            
            assert serializer.codec_id == "protobuf"
            assert serializer.format_name == "Protobuf"
            assert "protobuf" in serializer.aliases
            assert serializer.is_binary_format is True
        except ImportError:
            pytest.skip("protobuf not installed")
    
    def test_parquet_metadata(self):
        """Test Parquet serializer metadata."""
        try:
            from exonware.xwformats import XWParquetSerializer
            serializer = XWParquetSerializer()
            
            assert serializer.codec_id == "parquet"
            assert serializer.format_name == "Parquet"
            assert "parquet" in serializer.aliases
            assert serializer.is_binary_format is True
        except ImportError:
            pytest.skip("pyarrow not installed")
    
    def test_hdf5_metadata(self):
        """Test HDF5 serializer metadata."""
        try:
            from exonware.xwformats import XWHdf5Serializer
            serializer = XWHdf5Serializer()
            
            assert serializer.codec_id == "hdf5"
            assert serializer.format_name == "HDF5"
            assert "hdf5" in serializer.aliases
            assert serializer.is_binary_format is True
        except ImportError:
            pytest.skip("h5py not installed")
    
    def test_ubjson_metadata(self):
        """Test UBJSON serializer metadata."""
        try:
            from exonware.xwformats import XWUbjsonSerializer
            serializer = XWUbjsonSerializer()
            
            assert serializer.codec_id == "ubjson"
            assert "ubjson" in serializer.aliases
        except ImportError:
            pytest.skip("ubjson not installed")


class TestSerializerCapabilities:
    """Test serializer capabilities."""
    
    def test_protobuf_capabilities(self):
        """Test Protobuf capabilities."""
        try:
            from exonware.xwformats import XWProtobufSerializer
            from exonware.xwsystem.io.defs import CodecCapability
            
            serializer = XWProtobufSerializer()
            caps = serializer.capabilities
            
            assert caps & CodecCapability.BIDIRECTIONAL
            assert caps & CodecCapability.SCHEMA
        except ImportError:
            pytest.skip("protobuf not installed")
    
    def test_parquet_capabilities(self):
        """Test Parquet capabilities."""
        try:
            from exonware.xwformats import XWParquetSerializer
            from exonware.xwsystem.io.defs import CodecCapability
            
            serializer = XWParquetSerializer()
            caps = serializer.capabilities
            
            assert caps & CodecCapability.BIDIRECTIONAL
            assert caps & CodecCapability.SCHEMA
        except ImportError:
            pytest.skip("pyarrow not installed")


class TestSerializerFileExtensions:
    """Test serializer file extension handling."""
    
    def test_protobuf_extensions(self):
        """Test Protobuf file extensions."""
        try:
            from exonware.xwformats import XWProtobufSerializer
            serializer = XWProtobufSerializer()
            
            exts = serializer.file_extensions
            assert ".proto" in exts or ".pb" in exts
        except ImportError:
            pytest.skip("protobuf not installed")
    
    def test_parquet_extensions(self):
        """Test Parquet file extensions."""
        try:
            from exonware.xwformats import XWParquetSerializer
            serializer = XWParquetSerializer()
            
            exts = serializer.file_extensions
            assert ".parquet" in exts
        except ImportError:
            pytest.skip("pyarrow not installed")
    
    def test_hdf5_extensions(self):
        """Test HDF5 file extensions."""
        try:
            from exonware.xwformats import XWHdf5Serializer
            serializer = XWHdf5Serializer()
            
            exts = serializer.file_extensions
            assert ".h5" in exts or ".hdf5" in exts
        except ImportError:
            pytest.skip("h5py not installed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


