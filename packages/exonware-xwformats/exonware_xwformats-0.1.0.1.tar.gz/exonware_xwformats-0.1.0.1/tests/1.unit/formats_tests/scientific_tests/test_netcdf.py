#!/usr/bin/env python3
"""
Unit tests for NetCDF serializer in xwformats.
"""

import pytest

pytest.importorskip("netCDF4")

from exonware.xwformats.formats.scientific import XWNetcdfSerializer


@pytest.mark.xwformats_unit
class TestNetCDFSerializer:
    """Unit tests for NetCDF serializer."""

    def test_serializer_initialization(self):
        serializer = XWNetcdfSerializer()
        assert serializer.codec_id == "netcdf"
        assert ".nc" in serializer.file_extensions

    def test_encode_raises_not_implemented(self):
        serializer = XWNetcdfSerializer()
        with pytest.raises(NotImplementedError, match="file-based operations"):
            serializer.encode({"dimensions": {"time": 10}})

    def test_decode_raises_not_implemented(self):
        serializer = XWNetcdfSerializer()
        with pytest.raises(NotImplementedError, match="file-based operations"):
            serializer.decode(b"dummy")

    def test_encode_to_file_basic(self, tmp_path):
        serializer = XWNetcdfSerializer()
        output_file = tmp_path / "test.nc"
        data = {
            "dimensions": {"time": 10, "x": 5},
            "variables": {
                "temperature": {
                    "data": [[15.0] * 5 for _ in range(10)],
                    "dtype": "f4",
                    "dimensions": ("time", "x"),
                    "attributes": {"units": "Celsius"},
                }
            },
            "attributes": {"description": "Test data"},
        }

        serializer.encode_to_file(data, output_file)
        assert output_file.exists()

    def test_decode_from_file_basic(self, tmp_path):
        serializer = XWNetcdfSerializer()
        output_file = tmp_path / "test.nc"
        data = {
            "dimensions": {"time": 10, "x": 5},
            "variables": {
                "temperature": {
                    "data": [[15.0] * 5 for _ in range(10)],
                    "dtype": "f4",
                    "dimensions": ("time", "x"),
                    "attributes": {"units": "Celsius"},
                }
            },
            "attributes": {"description": "Test data"},
        }

        serializer.encode_to_file(data, output_file)
        result = serializer.decode_from_file(output_file)

        assert result["dimensions"]["time"] == 10
        assert result["dimensions"]["x"] == 5
        assert "temperature" in result["variables"]

    def test_roundtrip_file_operations(self, tmp_path):
        serializer = XWNetcdfSerializer()
        output_file = tmp_path / "roundtrip.nc"
        original = {
            "dimensions": {"lat": 3, "lon": 4},
            "variables": {
                "data_var": {
                    "data": [[1.0, 2.0, 3.0, 4.0] for _ in range(3)],
                    "dtype": "f8",
                    "dimensions": ("lat", "lon"),
                }
            },
            "attributes": {"title": "Test Dataset"},
        }

        serializer.encode_to_file(original, output_file)
        decoded = serializer.decode_from_file(output_file)

        assert decoded["dimensions"]["lat"] == 3
        assert decoded["dimensions"]["lon"] == 4
        assert "data_var" in decoded["variables"]

    def test_mime_types(self):
        serializer = XWNetcdfSerializer()
        assert "application/netcdf" in serializer.media_types
        assert "application/x-netcdf" in serializer.media_types

