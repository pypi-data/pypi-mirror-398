#!/usr/bin/env python3
"""
Unit tests for UBJSON serializer in xwformats.
"""

import pytest

pytest.importorskip("ubjson")

from exonware.xwformats.formats.binary import XWUbjsonSerializer


@pytest.mark.xwformats_unit
class TestUBJSONSerializer:
    """Unit tests for UBJSON serializer."""

    def test_serializer_initialization(self):
        serializer = XWUbjsonSerializer()
        assert serializer.codec_id == "ubjson"
        assert ".ubjson" in serializer.file_extensions

    def test_encode_simple_dict(self):
        serializer = XWUbjsonSerializer()
        data = {"name": "Alice", "age": 30}
        result = serializer.encode(data)
        assert isinstance(result, bytes)

    def test_decode_ubjson_bytes(self):
        serializer = XWUbjsonSerializer()
        data = {"name": "Alice", "age": 30}
        encoded = serializer.encode(data)
        decoded = serializer.decode(encoded)
        assert decoded == data

    def test_roundtrip_encoding(self):
        serializer = XWUbjsonSerializer()
        original = {
            "string": "value",
            "number": 42,
            "float": 3.14,
            "boolean": True,
            "null": None,
            "array": [1, 2, 3],
            "nested": {"key": "value"},
        }
        encoded = serializer.encode(original)
        decoded = serializer.decode(encoded)
        assert decoded == original

    def test_binary_format_is_compact(self):
        serializer = XWUbjsonSerializer()
        data = {"key": "value", "number": 42}
        encoded = serializer.encode(data)
        assert isinstance(encoded, bytes)
        assert len(encoded) <= len('{"key": "value", "number": 42}')

    def test_encode_list(self):
        serializer = XWUbjsonSerializer()
        data = [1, 2, 3, 4, 5]
        encoded = serializer.encode(data)
        decoded = serializer.decode(encoded)
        assert decoded == data

    def test_encode_nested_structures(self):
        serializer = XWUbjsonSerializer()
        data = {
            "users": [
                {"id": 1, "name": "Alice", "active": True},
                {"id": 2, "name": "Bob", "active": False},
            ],
            "metadata": {"version": 1.0, "count": 2},
        }
        encoded = serializer.encode(data)
        decoded = serializer.decode(encoded)
        assert decoded == data

    def test_mime_types(self):
        serializer = XWUbjsonSerializer()
        assert "application/ubjson" in serializer.media_types

    def test_file_extensions(self):
        serializer = XWUbjsonSerializer()
        assert ".ubj" in serializer.file_extensions
        assert ".ubjson" in serializer.file_extensions

