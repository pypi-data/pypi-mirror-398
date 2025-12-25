#!/usr/bin/env python3
"""
Unit tests for MATLAB MAT serializer in xwformats.
"""

import pytest

pytest.importorskip("scipy.io")

from exonware.xwformats.formats.scientific import XWMatSerializer


@pytest.mark.xwformats_unit
class TestMATSerializer:
    """Unit tests for MATLAB MAT serializer."""

    def test_serializer_initialization(self):
        serializer = XWMatSerializer()
        assert serializer.codec_id == "mat"
        assert ".mat" in serializer.file_extensions

    def test_encode_raises_not_implemented(self):
        serializer = XWMatSerializer()
        with pytest.raises(NotImplementedError, match="MAT encoding to bytes not supported"):
            serializer.encode({"array": [[1, 2]]})

    def test_encode_to_file_basic(self, tmp_path):
        serializer = XWMatSerializer()
        output_file = tmp_path / "test.mat"
        data = {"array": [[1, 2, 3], [4, 5, 6]], "scalar": 42, "string": "test"}

        serializer.encode_to_file(data, output_file)
        assert output_file.exists()

    def test_decode_from_file_basic(self, tmp_path):
        serializer = XWMatSerializer()
        output_file = tmp_path / "test.mat"
        data = {"array": [[1, 2, 3], [4, 5, 6]], "scalar": 42}

        serializer.encode_to_file(data, output_file)
        result = serializer.decode_from_file(output_file)

        assert "array" in result
        assert "scalar" in result

    def test_roundtrip_file_operations(self, tmp_path):
        serializer = XWMatSerializer()
        output_file = tmp_path / "roundtrip.mat"
        original = {
            "matrix": [[1.0, 2.0], [3.0, 4.0]],
            "vector": [10, 20, 30],
            "value": 3.14,
        }

        serializer.encode_to_file(original, output_file)
        decoded = serializer.decode_from_file(output_file)

        assert "matrix" in decoded
        assert "vector" in decoded
        assert "value" in decoded

    def test_encode_non_dict_wraps_in_dict(self, tmp_path):
        serializer = XWMatSerializer()
        output_file = tmp_path / "wrapped.mat"
        serializer.encode_to_file([1, 2, 3], output_file)
        decoded = serializer.decode_from_file(output_file)
        assert "data" in decoded

    def test_encode_with_compression(self, tmp_path):
        serializer = XWMatSerializer()
        output_file = tmp_path / "compressed.mat"
        data = {"large_array": [[i * j for j in range(20)] for i in range(20)]}

        serializer.encode_to_file(data, output_file, options={"do_compression": True})
        assert output_file.exists()

    def test_mime_types(self):
        serializer = XWMatSerializer()
        assert "application/x-matlab-data" in serializer.media_types
        assert "application/matlab" in serializer.media_types

