#!/usr/bin/env python3
#exonware/xwformats/src/exonware/xwformats/formats/database/leveldb.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 02-Nov-2025

LevelDB Serialization - Pure Python Key-Value Store (SQLite-based)

LevelDB-compatible serializer using SQLite as the backend engine.
SQLite is built into Python and provides:
- Cross-platform compatibility (Windows, Linux, macOS, Replit)
- No C++ build tools required
- Fast key-value operations with B-tree indexes
- ACID transactions
- Sorted key storage
- Thread-safe operations
- Widely used (millions of applications)

This implementation provides LevelDB-compatible API while using SQLite
internally for maximum portability and ease of deployment.

Following I→A→XW pattern:
- I: ISerialization (interface)
- A: ASerialization (abstract base)
- XW: XWLeveldbSerializer (concrete implementation)

Priority 1 (Security): Secure file operations with path validation and transaction safety
Priority 2 (Usability): Simple key-value API compatible with LevelDB interface
Priority 3 (Maintainability): Clean, well-structured pure Python code following design patterns
Priority 4 (Performance): Fast SQLite-backed operations with optimized indexes
Priority 5 (Extensibility): Supports LevelDB-compatible options and extensions
"""

from typing import Any, Optional, Union
from pathlib import Path
import pickle
import sqlite3
import threading

from exonware.xwsystem.io.serialization.base import ASerialization
from exonware.xwsystem.io.contracts import EncodeOptions, DecodeOptions
from exonware.xwsystem.io.defs import CodecCapability
from exonware.xwsystem.io.errors import SerializationError


class XWLeveldbSerializer(ASerialization):
    """
    LevelDB serializer - Pure Python implementation using SQLite.
    
    I: ISerialization (interface)
    A: ASerialization (abstract base)
    XW: XWLeveldbSerializer (concrete implementation)
    
    This implementation provides LevelDB-compatible functionality using SQLite:
    - Ordered key-value storage with sorted keys
    - Fast sequential and random reads
    - Efficient batch writes with transactions
    - Thread-safe operations
    - ACID compliance
    - Zero external dependencies (SQLite built into Python)
    
    LevelDB stores data in a directory. This implementation uses a single SQLite
    database file for simplicity while maintaining LevelDB API compatibility.
    """
    
    def __init__(self):
        """Initialize LevelDB serializer."""
        super().__init__()
        # Thread-local storage for database connections
        self._local = threading.local()
    
    @property
    def codec_id(self) -> str:
        """Codec identifier."""
        return "leveldb"
    
    @property
    def media_types(self) -> list[str]:
        """Supported MIME types."""
        return ["application/x-leveldb"]
    
    @property
    def file_extensions(self) -> list[str]:
        """Supported file extensions."""
        return [".ldb", ".leveldb"]
    
    @property
    def format_name(self) -> str:
        """Format name."""
        return "LevelDB"
    
    @property
    def mime_type(self) -> str:
        """Primary MIME type."""
        return "application/x-leveldb"
    
    @property
    def is_binary_format(self) -> bool:
        """LevelDB is a binary format."""
        return True
    
    @property
    def supports_streaming(self) -> bool:
        """LevelDB supports streaming operations."""
        return True
    
    @property
    def capabilities(self) -> CodecCapability:
        """LevelDB supports bidirectional operations."""
        return CodecCapability.BIDIRECTIONAL
    
    @property
    def aliases(self) -> list[str]:
        """LevelDB aliases."""
        return ["leveldb", "LevelDB", "ldb"]
    
    def encode(self, value: Any, *, options: Optional[EncodeOptions] = None) -> bytes:
        """
        Encode data to LevelDB-compatible bytes.
        
        Note: LevelDB is designed for file-based operations. This method
        pickles the data for transport when not using file-based operations.
        
        Args:
            value: Dictionary of key-value pairs (expected)
            options: Encoding options
            
        Returns:
            Pickled bytes representation
            
        Raises:
            SerializationError: If value is not a dictionary
        """
        if not isinstance(value, dict):
            raise SerializationError(
                f"LevelDB encode expects dict, got {type(value).__name__}. "
                "For full LevelDB features (sorted keys, batch operations), use save_file().",
                self.format_name
            )
        
        # For in-memory transport, pickle the dictionary
        return pickle.dumps(value)
    
    def decode(self, repr: Union[bytes, str], *, options: Optional[DecodeOptions] = None) -> Any:
        """
        Decode LevelDB bytes to Python data.
        
        Note: LevelDB is designed for file-based operations. This method
        unpickles data that was encoded for transport.
        
        Args:
            repr: Pickled bytes representation
            options: Decoding options
            
        Returns:
            Dictionary of key-value pairs
            
        Raises:
            SerializationError: If decoding fails
        """
        if isinstance(repr, str):
            raise SerializationError(
                "LevelDB decode expects bytes, got string. "
                "For full LevelDB features, use load_file().",
                self.format_name
            )
        
        try:
            return pickle.loads(repr)
        except (pickle.UnpicklingError, EOFError, AttributeError) as e:
            raise SerializationError(
                f"Failed to decode LevelDB data: {e}",
                self.format_name,
                e
            ) from e
    
    def _get_db_file_path(self, file_path: Union[str, Path]) -> Path:
        """
        Get validated database file path.
        
        LevelDB uses directories, but we use a single SQLite file.
        If a directory is provided, create/use a database file inside it.
        
        Args:
            file_path: Path to LevelDB database directory or SQLite file
            
        Returns:
            Validated Path to SQLite database file
            
        Raises:
            SerializationError: If path validation fails
        """
        path = Path(file_path).resolve()
        
        # If it's a directory, create a database file inside
        if path.is_dir():
            db_file = path / "leveldb.sqlite"
        elif path.suffix in ['.ldb', '.leveldb']:
            # Treat as directory name (LevelDB convention)
            if path.exists() and path.is_file():
                db_file = path
            else:
                # Create directory and database file inside
                path.mkdir(parents=True, exist_ok=True)
                db_file = path / "leveldb.sqlite"
        else:
            # Assume it's a file path
            db_file = path
        
        # Security: Validate parent directory (GUIDE_DEV.md Priority #1)
        parent = db_file.parent
        if parent.exists() and not parent.is_dir():
            raise SerializationError(
                f"LevelDB database parent path is not a directory: {parent}",
                self.format_name
            )
        
        return db_file
    
    def _get_connection(self, db_file: Path, create_if_missing: bool = True) -> sqlite3.Connection:
        """
        Get thread-local SQLite connection with proper setup.
        
        Args:
            db_file: Path to SQLite database file
            create_if_missing: Whether to create database if it doesn't exist
            
        Returns:
            SQLite connection object
            
        Raises:
            SerializationError: If connection fails
        """
        # Use thread-local storage for connections
        if not hasattr(self._local, 'connections'):
            self._local.connections = {}
        
        db_str = str(db_file.resolve())
        
        # Reuse existing connection if available
        if db_str in self._local.connections:
            conn = self._local.connections[db_str]
            # Check if connection is still valid
            try:
                conn.execute("SELECT 1")
                return conn
            except sqlite3.ProgrammingError:
                # Connection closed, remove and recreate
                del self._local.connections[db_str]
        
        # Create parent directory if needed
        if create_if_missing:
            db_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Create connection with optimizations
            conn = sqlite3.connect(
                db_str,
                check_same_thread=False,  # Allow use across threads
                timeout=30.0  # 30 second timeout for locks
            )
            
            # Enable write-ahead logging for better concurrency
            conn.execute("PRAGMA journal_mode=WAL")
            
            # Optimize for performance
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=10000")
            conn.execute("PRAGMA temp_store=MEMORY")
            
            # Create table if not exists
            conn.execute('''
                CREATE TABLE IF NOT EXISTS kv_store (
                    key BLOB PRIMARY KEY,
                    value BLOB NOT NULL,
                    created_at REAL DEFAULT (julianday('now'))
                )
            ''')
            
            # Create index for sorted key access (LevelDB maintains sorted order)
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_key_sorted ON kv_store(key)
            ''')
            
            # Store connection in thread-local storage
            self._local.connections[db_str] = conn
            
            return conn
            
        except sqlite3.Error as e:
            raise SerializationError(
                f"Failed to connect to LevelDB database: {e}",
                self.format_name,
                e
            ) from e
    
    def _close_connection(self, db_file: Path) -> None:
        """
        Close thread-local SQLite connection.
        
        Args:
            db_file: Path to SQLite database file
        """
        if hasattr(self._local, 'connections'):
            db_str = str(db_file.resolve())
            if db_str in self._local.connections:
                try:
                    self._local.connections[db_str].close()
                except sqlite3.Error:
                    pass  # Already closed or invalid
                finally:
                    del self._local.connections[db_str]
    
    def _serialize_key(self, key: Any) -> bytes:
        """
        Serialize key to bytes.
        
        Uses type markers to preserve key types:
        - String keys: UTF-8 encoded (no marker)
        - Bytes keys: Prefixed with \x00 marker
        - Other keys: Pickled and prefixed with \x01 marker
        
        Args:
            key: Key to serialize (str, bytes, or pickleable object)
            
        Returns:
            Bytes representation of key with type marker
        """
        if isinstance(key, bytes):
            # Prefix bytes keys with \x00 to distinguish from strings
            return b'\x00' + key
        elif isinstance(key, str):
            # String keys: UTF-8 encoded (no marker needed)
            return key.encode('utf-8')
        else:
            # For non-string/bytes keys, pickle and prefix with \x01
            return b'\x01' + pickle.dumps(key)
    
    def _deserialize_key(self, key_bytes: bytes) -> Any:
        """
        Deserialize key from bytes.
        
        Uses type markers to restore original key types:
        - \x00 prefix: Bytes key
        - \x01 prefix: Pickled key
        - No prefix: String key (UTF-8)
        
        Args:
            key_bytes: Bytes representation of key with type marker
            
        Returns:
            Deserialized key (str, bytes, or unpickled object)
        """
        if not key_bytes:
            return key_bytes
        
        # Check for type markers
        if key_bytes[0] == 0x00:
            # Bytes key: remove marker and return bytes
            return key_bytes[1:]
        elif key_bytes[0] == 0x01:
            # Pickled key: remove marker and unpickle
            try:
                return pickle.loads(key_bytes[1:])
            except (pickle.UnpicklingError, EOFError):
                # If unpickling fails, return bytes as-is (without marker)
                return key_bytes[1:]
        else:
            # No marker: try UTF-8 decode (string key)
            try:
                return key_bytes.decode('utf-8')
            except UnicodeDecodeError:
                # If not valid UTF-8, return bytes as-is
                return key_bytes
    
    def _serialize_value(self, value: Any) -> bytes:
        """
        Serialize value to bytes.
        
        Args:
            value: Value to serialize (any pickleable object)
            
        Returns:
            Bytes representation of value
        """
        return pickle.dumps(value)
    
    def _deserialize_value(self, value_bytes: bytes) -> Any:
        """
        Deserialize value from bytes.
        
        Args:
            value_bytes: Bytes representation of value
            
        Returns:
            Deserialized value
        """
        try:
            return pickle.loads(value_bytes)
        except (pickle.UnpicklingError, EOFError, AttributeError) as e:
            raise SerializationError(
                f"Failed to deserialize LevelDB value: {e}",
                self.format_name,
                e
            ) from e
    
    def save_file(
        self,
        value: Any,
        file_path: Union[str, Path],
        **options
    ) -> None:
        """
        Save data to LevelDB database file.
        
        LevelDB stores data in a directory containing multiple files.
        This implementation uses SQLite for storage while maintaining
        LevelDB API compatibility.
        
        Args:
            value: Dictionary of key-value pairs to store
            file_path: Path to LevelDB database directory or SQLite file
            **options: Encoding options:
                - create_if_missing (bool): Create database if it doesn't exist (default: True)
                - overwrite (bool): Clear existing database before writing (default: False)
                - error_if_exists (bool): Raise error if database exists (default: False)
                - sync (bool): Sync writes to disk immediately (default: True)
        
        Raises:
            SerializationError: If value is not a dictionary or database operation fails
        """
        if not isinstance(value, dict):
            raise SerializationError(
                f"LevelDB save_file expects dict, got {type(value).__name__}",
                self.format_name
            )
        
        create_if_missing = options.get('create_if_missing', True)
        overwrite = options.get('overwrite', False)
        error_if_exists = options.get('error_if_exists', False)
        sync = options.get('sync', True)
        
        db_file = self._get_db_file_path(file_path)
        
        # Check if database exists
        if db_file.exists() and error_if_exists:
            raise SerializationError(
                f"LevelDB database already exists: {db_file}",
                self.format_name
            )
        
        if not db_file.exists() and not create_if_missing:
            raise SerializationError(
                f"LevelDB database does not exist: {db_file}",
                self.format_name
            )
        
        conn = None
        try:
            conn = self._get_connection(db_file, create_if_missing=create_if_missing)
            
            # Use transaction for atomic writes
            with conn:
                # Clear existing data if overwrite requested
                if overwrite:
                    conn.execute("DELETE FROM kv_store")
                
                # Write all key-value pairs in batch
                for key, val in value.items():
                    key_bytes = self._serialize_key(key)
                    value_bytes = self._serialize_value(val)
                    
                    # Insert or replace
                    conn.execute(
                        "INSERT OR REPLACE INTO kv_store (key, value) VALUES (?, ?)",
                        (key_bytes, value_bytes)
                    )
            
            # Sync to disk if requested (after transaction commits)
            # Use PASSIVE checkpoint to avoid blocking other connections
            if sync and conn:
                try:
                    # Commit any pending changes first
                    conn.commit()
                    # WAL checkpoint (PASSIVE is non-blocking, FULL can lock)
                    conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
                except sqlite3.Error:
                    # Ignore checkpoint errors - they're not critical for correctness
                    pass
                
        except sqlite3.Error as e:
            raise SerializationError(
                f"LevelDB save_file failed: {e}",
                self.format_name,
                e
            ) from e
    
    def load_file(
        self,
        file_path: Union[str, Path],
        **options
    ) -> dict[str, Any]:
        """
        Load data from LevelDB database file.
        
        LevelDB stores data in a directory containing multiple files.
        This implementation reads from SQLite database while maintaining
        LevelDB API compatibility.
        
        Args:
            file_path: Path to LevelDB database directory or SQLite file
            **options: Decoding options:
                - create_if_missing (bool): Create database if it doesn't exist (default: False)
                - fill_cache (bool): Fill read cache (default: True, SQLite handles this)
                - verify_checksums (bool): Verify data integrity (default: False)
        
        Returns:
            Dictionary of all key-value pairs (sorted by key order)
            
        Raises:
            SerializationError: If database doesn't exist or read operation fails
        """
        create_if_missing = options.get('create_if_missing', False)
        verify_checksums = options.get('verify_checksums', False)
        
        db_file = self._get_db_file_path(file_path)
        
        if not db_file.exists() and not create_if_missing:
            raise SerializationError(
                f"LevelDB database does not exist: {db_file}",
                self.format_name
            )
        
        conn = None
        try:
            conn = self._get_connection(db_file, create_if_missing=create_if_missing)
            
            result = {}
            
            # Read all key-value pairs in sorted order (LevelDB maintains sorted keys)
            cursor = conn.execute(
                "SELECT key, value FROM kv_store ORDER BY key"
            )
            
            for row in cursor:
                key_bytes, value_bytes = row
                key = self._deserialize_key(key_bytes)
                value = self._deserialize_value(value_bytes)
                result[key] = value
            
            # Verify checksums if requested
            if verify_checksums:
                # SQLite provides built-in integrity checks
                integrity_check = conn.execute("PRAGMA integrity_check").fetchone()
                if integrity_check[0] != 'ok':
                    raise SerializationError(
                        f"LevelDB database integrity check failed: {integrity_check[0]}",
                        self.format_name
                    )
            
            return result
            
        except sqlite3.Error as e:
            raise SerializationError(
                f"LevelDB load_file failed: {e}",
                self.format_name,
                e
            ) from e
    
    # Convenience methods for backward compatibility with tests
    def encode_to_file(
        self, 
        data: Any, 
        file_path: Union[str, Path], 
        options: Optional[dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """
        Encode data to LevelDB database file (convenience method).
        
        This is an alias for save_file() for backward compatibility.
        
        Args:
            data: Dictionary of key-value pairs to store
            file_path: Path to LevelDB database directory or SQLite file
            options: Encoding options (dict format)
            **kwargs: Additional encoding options (merged with options dict)
        """
        opts = options or {}
        # Merge kwargs into options (kwargs take precedence)
        opts.update(kwargs)
        self.save_file(data, file_path, **opts)
    
    def decode_from_file(self, file_path: Union[str, Path], options: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """
        Decode LevelDB database file to Python dict (convenience method).
        
        This is an alias for load_file() for backward compatibility.
        
        Args:
            file_path: Path to LevelDB database directory or SQLite file
            options: Decoding options (dict format)
            
        Returns:
            Dictionary of all key-value pairs
        """
        opts = options or {}
        return self.load_file(file_path, **opts)


# Backward compatibility alias
LeveldbSerializer = XWLeveldbSerializer
