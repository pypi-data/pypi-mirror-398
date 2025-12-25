"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: November 2, 2025

GraphDB serialization - Graph database serialization.

Following I→A→XW pattern:
- I: ISerialization (interface)
- A: ASerialization (abstract base)
- XW: XWGraphDbSerializer (concrete implementation)
"""

from typing import Any, Optional, Union
from pathlib import Path

from exonware.xwsystem.io.serialization.base import ASerialization
from exonware.xwsystem.io.contracts import EncodeOptions, DecodeOptions
from exonware.xwsystem.io.defs import CodecCapability
from exonware.xwsystem.io.errors import SerializationError


class XWGraphDbSerializer(ASerialization):
    """GraphDB serializer - follows I→A→XW pattern."""
    
    @property
    def codec_id(self) -> str:
        return "graphdb"
    
    @property
    def media_types(self) -> list[str]:
        return ["application/x-graph"]
    
    @property
    def file_extensions(self) -> list[str]:
        return [".graph", ".graphdb"]
    
    @property
    def format_name(self) -> str:
        return "GraphDB"
    
    @property
    def mime_type(self) -> str:
        return "application/x-graph"
    
    @property
    def is_binary_format(self) -> bool:
        return True
    
    @property
    def supports_streaming(self) -> bool:
        return False
    
    @property
    def capabilities(self) -> CodecCapability:
        return CodecCapability.BIDIRECTIONAL
    
    @property
    def aliases(self) -> list[str]:
        return ["graphdb", "graph"]
    
    def encode(self, value: Any, *, options: Optional[EncodeOptions] = None) -> Union[bytes, str]:
        """GraphDB encode requires database connection - use save_file() instead."""
        raise NotImplementedError("GraphDB requires database operations - use save_file()")
    
    def decode(self, repr: Union[bytes, str], *, options: Optional[DecodeOptions] = None) -> Any:
        """GraphDB decode requires database connection - use load_file() instead."""
        raise NotImplementedError("GraphDB requires database operations - use load_file()")


GraphDbSerializer = XWGraphDbSerializer

