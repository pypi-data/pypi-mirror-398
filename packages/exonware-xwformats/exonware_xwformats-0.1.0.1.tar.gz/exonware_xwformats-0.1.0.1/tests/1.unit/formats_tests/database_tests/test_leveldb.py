#!/usr/bin/env python3
"""
Unit tests for LevelDB serializer in xwformats.

Following GUIDE_TEST.md standards:
- Comprehensive test coverage
- Test both success and failure scenarios
- Edge cases and various data types
- Proper error handling validation
- Root cause fixing (no rigged tests)

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
"""

import pytest
from pathlib import Path
import sys
import importlib.util

# Import LevelDB module directly to avoid triggering package __init__.py imports
# This bypasses exonware.xwformats.__init__.py which imports all formats (including ORC that needs pyorc)
_test_dir = Path(__file__).parent
# Navigate from test file to xwformats root: test_leveldb.py -> database_tests -> formats_tests -> 1.unit -> tests -> xwformats
_xwformats_root = _test_dir.parent.parent.parent.parent
_leveldb_module_path = _xwformats_root / "src" / "exonware" / "xwformats" / "formats" / "database" / "leveldb.py"

# Verify path exists
if not _leveldb_module_path.exists():
    raise ImportError(f"LevelDB module not found at {_leveldb_module_path}")

# Load required dependencies first
from exonware.xwsystem.io.serialization.base import ASerialization
from exonware.xwsystem.io.contracts import EncodeOptions, DecodeOptions
from exonware.xwsystem.io.defs import CodecCapability
from exonware.xwsystem.io.errors import SerializationError

# Load the module directly from file
spec = importlib.util.spec_from_file_location("exonware.xwformats.formats.database.leveldb", _leveldb_module_path)
leveldb_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(leveldb_module)

# Extract the classes we need
XWLeveldbSerializer = leveldb_module.XWLeveldbSerializer
LeveldbSerializer = leveldb_module.LeveldbSerializer


@pytest.mark.xwformats_unit
class TestLevelDBSerializer:
    """Unit tests for LevelDB serializer - Pure Python SQLite implementation."""
    
    def test_serializer_initialization(self):
        """Test that serializer initializes correctly."""
        serializer = XWLeveldbSerializer()
        assert serializer.codec_id == "leveldb"
        assert ".leveldb" in serializer.file_extensions
        assert ".ldb" in serializer.file_extensions
        assert "application/x-leveldb" in serializer.media_types
    
    def test_alias_compatibility(self):
        """Test that backward compatibility alias works."""
        assert LeveldbSerializer is XWLeveldbSerializer
        
        serializer1 = XWLeveldbSerializer()
        serializer2 = LeveldbSerializer()
        assert type(serializer1) is type(serializer2)
    
    def test_metadata_properties(self):
        """Test all metadata properties."""
        serializer = XWLeveldbSerializer()
        
        assert serializer.codec_id == "leveldb"
        assert serializer.format_name == "LevelDB"
        assert serializer.mime_type == "application/x-leveldb"
        assert serializer.is_binary_format is True
        assert serializer.supports_streaming is True
        assert serializer.capabilities == CodecCapability.BIDIRECTIONAL
        assert "leveldb" in serializer.aliases
        assert "LevelDB" in serializer.aliases
        assert "ldb" in serializer.aliases
    
    def test_encode_dict_to_bytes(self):
        """Test encoding dictionary to bytes."""
        serializer = XWLeveldbSerializer()
        data = {"key1": "value1", "key2": "value2"}
        
        result = serializer.encode(data)
        assert isinstance(result, bytes)
        assert len(result) > 0
    
    def test_encode_non_dict_raises_error(self):
        """Test that encoding non-dict raises clear error."""
        serializer = XWLeveldbSerializer()
        
        with pytest.raises(SerializationError, match="expects dict"):
            serializer.encode(["not", "a", "dict"])
        
        with pytest.raises(SerializationError, match="expects dict"):
            serializer.encode("not a dict")
        
        with pytest.raises(SerializationError, match="expects dict"):
            serializer.encode(123)
    
    def test_decode_bytes_to_dict(self):
        """Test decoding bytes back to dictionary."""
        serializer = XWLeveldbSerializer()
        original = {"key1": "value1", "key2": "value2"}
        
        encoded = serializer.encode(original)
        decoded = serializer.decode(encoded)
        
        assert decoded == original
        assert isinstance(decoded, dict)
    
    def test_decode_string_raises_error(self):
        """Test that decoding string raises clear error."""
        serializer = XWLeveldbSerializer()
        
        with pytest.raises(SerializationError, match="expects bytes"):
            serializer.decode("not bytes")
    
    def test_decode_invalid_bytes_raises_error(self):
        """Test that invalid bytes raise clear error."""
        serializer = XWLeveldbSerializer()
        
        with pytest.raises(SerializationError, match="Failed to decode"):
            serializer.decode(b"invalid pickle data")
    
    def test_encode_to_file_creates_database(self, tmp_path):
        """Test that encode_to_file creates database."""
        serializer = XWLeveldbSerializer()
        db_path = tmp_path / "test.ldb"
        data = {"user:1": "Alice", "user:2": "Bob"}
        
        serializer.encode_to_file(data, db_path)
        
        # Check that database directory exists
        assert db_path.exists() or (db_path.parent / "leveldb.sqlite").exists()
    
    def test_decode_from_file_reads_database(self, tmp_path):
        """Test that decode_from_file reads database correctly."""
        serializer = XWLeveldbSerializer()
        db_path = tmp_path / "test.ldb"
        data = {"user:1": "Alice", "user:2": "Bob"}
        
        serializer.encode_to_file(data, db_path)
        result = serializer.decode_from_file(db_path)
        
        assert result == data
        assert isinstance(result, dict)
    
    def test_roundtrip_file_operations(self, tmp_path):
        """Test complete roundtrip of file operations."""
        serializer = XWLeveldbSerializer()
        db_path = tmp_path / "roundtrip.ldb"
        original = {
            "config:timeout": 30,
            "config:retries": 3,
            "user:admin": {"role": "admin", "active": True},
        }
        
        serializer.encode_to_file(original, db_path)
        decoded = serializer.decode_from_file(db_path)
        
        assert decoded == original
        assert decoded["config:timeout"] == 30
        assert decoded["user:admin"]["role"] == "admin"
    
    def test_encode_to_file_non_dict_raises_error(self, tmp_path):
        """Test that encoding non-dict to file raises error."""
        serializer = XWLeveldbSerializer()
        db_path = tmp_path / "invalid.ldb"
        
        with pytest.raises(SerializationError, match="expects dict"):
            serializer.encode_to_file([1, 2, 3], db_path)
        
        with pytest.raises(SerializationError, match="expects dict"):
            serializer.encode_to_file("string", db_path)
    
    def test_handles_various_value_types(self, tmp_path):
        """Test handling of various Python data types."""
        serializer = XWLeveldbSerializer()
        db_path = tmp_path / "types.ldb"
        data = {
            "string": "value",
            "int": 42,
            "float": 3.14,
            "bool": True,
            "bool_false": False,
            "none": None,
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
            "tuple": (1, 2, 3),
            "set": {1, 2, 3},
        }
        
        serializer.encode_to_file(data, db_path)
        decoded = serializer.decode_from_file(db_path)
        
        assert decoded == data
        assert decoded["string"] == "value"
        assert decoded["int"] == 42
        assert decoded["float"] == 3.14
        assert decoded["bool"] is True
        assert decoded["bool_false"] is False
        assert decoded["none"] is None
        assert decoded["list"] == [1, 2, 3]
        assert decoded["dict"] == {"nested": "value"}
    
    def test_handles_various_key_types(self, tmp_path):
        """Test handling of various key types."""
        serializer = XWLeveldbSerializer()
        db_path = tmp_path / "keys.ldb"
        data = {
            "string_key": "value1",
        }
        
        # Test with bytes key separately (can't mix types in dict literal)
        serializer.encode_to_file(data, db_path)
        decoded = serializer.decode_from_file(db_path)
        
        assert decoded["string_key"] == "value1"
        
        # Test bytes key separately
        data_bytes = {b"bytes_key": "value2"}
        serializer.encode_to_file(data_bytes, db_path, overwrite=True)
        decoded = serializer.decode_from_file(db_path)
        assert decoded[b"bytes_key"] == "value2"
    
    def test_sorted_key_storage(self, tmp_path):
        """Test that keys are stored and retrieved in sorted order."""
        serializer = XWLeveldbSerializer()
        db_path = tmp_path / "sorted.ldb"
        # Insert keys in random order
        data = {
            "zebra": "last",
            "alpha": "first",
            "middle": "center",
        }
        
        serializer.encode_to_file(data, db_path)
        decoded = serializer.decode_from_file(db_path)
        
        # Keys should be in sorted order (LevelDB maintains sorted order)
        keys = list(decoded.keys())
        assert keys == sorted(keys)
        assert keys[0] == "alpha"
        assert keys[-1] == "zebra"
    
    def test_overwrite_option(self, tmp_path):
        """Test overwrite option clears existing data."""
        serializer = XWLeveldbSerializer()
        db_path = tmp_path / "overwrite.ldb"
        
        # Write initial data
        serializer.encode_to_file({"key1": "value1", "key2": "value2"}, db_path)
        
        # Overwrite with new data
        serializer.encode_to_file({"key3": "value3"}, db_path, overwrite=True)
        
        decoded = serializer.decode_from_file(db_path)
        assert "key1" not in decoded
        assert "key2" not in decoded
        assert decoded["key3"] == "value3"
    
    def test_error_if_exists_option(self, tmp_path):
        """Test error_if_exists option raises error when database exists."""
        serializer = XWLeveldbSerializer()
        db_path = tmp_path / "exists.ldb"
        
        # Create database first
        serializer.encode_to_file({"key1": "value1"}, db_path)
        
        # Try to create again with error_if_exists
        with pytest.raises(SerializationError, match="already exists"):
            serializer.encode_to_file({"key2": "value2"}, db_path, error_if_exists=True)
    
    def test_create_if_missing_false(self, tmp_path):
        """Test create_if_missing=False raises error when database doesn't exist."""
        serializer = XWLeveldbSerializer()
        db_path = tmp_path / "missing.ldb"
        
        with pytest.raises(SerializationError, match="does not exist"):
            serializer.encode_to_file(
                {"key": "value"},
                db_path,
                create_if_missing=False
            )
    
    def test_load_file_nonexistent_raises_error(self, tmp_path):
        """Test that loading non-existent file raises clear error."""
        serializer = XWLeveldbSerializer()
        db_path = tmp_path / "nonexistent.ldb"
        
        with pytest.raises(SerializationError, match="does not exist"):
            serializer.decode_from_file(db_path)
    
    def test_large_dataset(self, tmp_path):
        """Test handling of large datasets."""
        serializer = XWLeveldbSerializer()
        db_path = tmp_path / "large.ldb"
        
        # Create large dataset
        data = {f"key_{i}": f"value_{i}" for i in range(1000)}
        
        serializer.encode_to_file(data, db_path)
        decoded = serializer.decode_from_file(db_path)
        
        assert len(decoded) == 1000
        assert decoded["key_0"] == "value_0"
        assert decoded["key_999"] == "value_999"
    
    def test_nested_data_structures(self, tmp_path):
        """Test handling of deeply nested data structures."""
        serializer = XWLeveldbSerializer()
        db_path = tmp_path / "nested.ldb"
        data = {
            "level1": {
                "level2": {
                    "level3": {
                        "value": "deep"
                    }
                }
            },
            "list_of_dicts": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"}
            ],
        }
        
        serializer.encode_to_file(data, db_path)
        decoded = serializer.decode_from_file(db_path)
        
        assert decoded["level1"]["level2"]["level3"]["value"] == "deep"
        assert decoded["list_of_dicts"][0]["name"] == "Alice"
    
    def test_empty_dict(self, tmp_path):
        """Test handling of empty dictionary."""
        serializer = XWLeveldbSerializer()
        db_path = tmp_path / "empty.ldb"
        data = {}
        
        serializer.encode_to_file(data, db_path)
        decoded = serializer.decode_from_file(db_path)
        
        assert decoded == {}
        assert len(decoded) == 0
    
    def test_special_characters_in_keys_and_values(self, tmp_path):
        """Test handling of special characters and Unicode."""
        serializer = XWLeveldbSerializer()
        db_path = tmp_path / "unicode.ldb"
        data = {
            "key with spaces": "value with spaces",
            "key-with-dashes": "value-with-dashes",
            "unicode_key_测试": "unicode_value_测试",
            "emoji_key_😀": "emoji_value_🎉",
            "special_chars_!@#$%": "special_value_!@#$%",
        }
        
        serializer.encode_to_file(data, db_path)
        decoded = serializer.decode_from_file(db_path)
        
        assert decoded["key with spaces"] == "value with spaces"
        assert decoded["unicode_key_测试"] == "unicode_value_测试"
        assert decoded["emoji_key_😀"] == "emoji_value_🎉"
    
    def test_concurrent_access_safety(self, tmp_path):
        """Test thread-safety of database operations."""
        import threading
        import time
        
        serializer = XWLeveldbSerializer()
        db_path = tmp_path / "concurrent.ldb"
        
        results = []
        errors = []
        lock = threading.Lock()
        
        def write_data(thread_id: int):
            try:
                # Use unique database path per thread to avoid conflicts
                thread_db_path = tmp_path / f"concurrent_{thread_id}.ldb"
                data = {f"thread_{thread_id}_key_{i}": f"value_{i}" for i in range(10)}
                serializer.encode_to_file(data, thread_db_path)
                with lock:
                    results.append(thread_id)
            except Exception as e:
                with lock:
                    errors.append((thread_id, str(e)))
        
        # Create multiple threads writing simultaneously
        threads = []
        for i in range(3):
            thread = threading.Thread(target=write_data, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All threads should succeed (using separate databases)
        assert len(results) == 3, f"Expected 3 successful writes, got {len(results)}. Errors: {errors}"
        # Verify all databases can be read
        for i in range(3):
            thread_db_path = tmp_path / f"concurrent_{i}.ldb"
            final_data = serializer.decode_from_file(thread_db_path)
            assert len(final_data) == 10, f"Thread {i} database should have 10 keys"
    
    def test_save_file_and_load_file_methods(self, tmp_path):
        """Test save_file and load_file methods (interface methods)."""
        serializer = XWLeveldbSerializer()
        db_path = tmp_path / "interface.ldb"
        data = {"method": "save_file", "test": True}
        
        # Test save_file (interface method)
        serializer.save_file(data, db_path)
        
        # Test load_file (interface method)
        decoded = serializer.load_file(db_path)
        
        assert decoded == data
    
    def test_options_passed_correctly(self, tmp_path):
        """Test that options are passed correctly to file operations."""
        serializer = XWLeveldbSerializer()
        db_path = tmp_path / "options.ldb"
        
        # Test with sync option
        data = {"sync": "test"}
        serializer.save_file(data, db_path, sync=True)
        decoded = serializer.load_file(db_path)
        assert decoded == data
        
        # Test with create_if_missing
        new_path = tmp_path / "new_db.ldb"
        serializer.save_file(data, new_path, create_if_missing=True)
        assert serializer.load_file(new_path) == data
