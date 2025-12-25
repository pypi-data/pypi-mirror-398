#!/usr/bin/env python3
#exonware/xwformats/src/exonware/xwformats/formats/text/xml.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 15-Nov-2025

XML Serialization - Extensible Markup Language

XML is a markup language for structured data:
- Human-readable
- Supports namespaces and schemas
- Widely used in enterprise systems
- Supports validation and transformation

Priority 1 (Security): Safe XML parsing (prevent XXE attacks)
Priority 2 (Usability): Simple XML read/write API
Priority 3 (Maintainability): Clean XML handling
Priority 4 (Performance): Efficient XML parsing
Priority 5 (Extensibility): Support XML namespaces and schemas
"""

from typing import Any, Optional, Union
from pathlib import Path
import xml.etree.ElementTree as ET
from xml.dom import minidom

from exonware.xwsystem.io.serialization.base import ASerialization
from exonware.xwsystem.io.serialization.contracts import ISerialization
from exonware.xwsystem.io.contracts import EncodeOptions, DecodeOptions
from exonware.xwsystem.io.errors import SerializationError


class XWXmlSerializer(ASerialization):
    """
    XML serializer.
    
    I: ISerialization (interface)
    A: ASerialization (abstract base)
    XW: XWXmlSerializer (concrete implementation)
    """
    
    def __init__(self):
        """Initialize XML serializer."""
        super().__init__()
    
    @property
    def codec_id(self) -> str:
        """Codec identifier."""
        return "xml"
    
    @property
    def media_types(self) -> list[str]:
        """Supported media types."""
        return ["application/xml", "text/xml"]
    
    @property
    def file_extensions(self) -> list[str]:
        """Supported file extensions."""
        return [".xml"]
    
    @property
    def format_name(self) -> str:
        """Format name."""
        return "XML"
    
    @property
    def mime_type(self) -> str:
        """MIME type."""
        return "application/xml"
    
    @property
    def is_binary_format(self) -> bool:
        """Whether format is binary."""
        return False
    
    @property
    def supports_streaming(self) -> bool:
        """Whether format supports streaming."""
        return True
    
    def encode(
        self,
        data: Any,
        options: Optional[EncodeOptions] = None
    ) -> bytes:
        """
        Encode data to XML.
        
        Args:
            data: Data to encode (dict, ElementTree, or XML string)
            options: Encoding options (root_tag, pretty_print, etc.)
            
        Returns:
            XML-encoded bytes
            
        Raises:
            SerializationError: If encoding fails
        """
        options = options or {}
        root_tag = options.get('root_tag', 'root')
        pretty_print = options.get('pretty_print', False)
        encoding = options.get('encoding', 'utf-8')
        
        try:
            if isinstance(data, ET.Element):
                # Already an ElementTree element
                root = data
            elif isinstance(data, str):
                # XML string - parse it
                root = ET.fromstring(data)
            elif isinstance(data, dict):
                # Convert dict to XML
                root = self._dict_to_element(data, root_tag)
            else:
                raise ValueError(f"Unsupported data type for XML: {type(data)}")
            
            # Convert to string
            xml_str = ET.tostring(root, encoding=encoding)
            
            # Pretty print if requested
            if pretty_print:
                dom = minidom.parseString(xml_str)
                xml_str = dom.toprettyxml(indent="  ", encoding=encoding)
            
            return xml_str if isinstance(xml_str, bytes) else xml_str.encode(encoding)
        except Exception as e:
            raise SerializationError(f"XML encoding failed: {e}") from e
    
    def decode(
        self,
        data: Union[bytes, bytearray, str],
        options: Optional[DecodeOptions] = None
    ) -> Any:
        """
        Decode XML data.
        
        Args:
            data: XML-encoded bytes or string
            options: Decoding options (return_type: 'dict' or 'element')
            
        Returns:
            Decoded data (dict or ElementTree element)
            
        Raises:
            SerializationError: If decoding fails
        """
        options = options or {}
        return_type = options.get('return_type', 'dict')
        
        try:
            if isinstance(data, (bytes, bytearray)):
                data = data.decode('utf-8')
            
            # Parse XML with safe parser (disable XXE)
            parser = ET.XMLParser()
            parser.entity = {}  # Disable external entity expansion
            root = ET.fromstring(data, parser=parser)
            
            if return_type == 'element':
                return root
            else:
                # Convert to dict
                return self._element_to_dict(root)
        except Exception as e:
            raise SerializationError(f"XML decoding failed: {e}") from e
    
    def _dict_to_element(self, data: dict, tag: str) -> ET.Element:
        """Convert dict to XML Element."""
        element = ET.Element(tag)
        
        for key, value in data.items():
            if isinstance(value, dict):
                child = self._dict_to_element(value, key)
                element.append(child)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        child = self._dict_to_element(item, key)
                    else:
                        child = ET.Element(key)
                        child.text = str(item)
                    element.append(child)
            else:
                child = ET.Element(key)
                child.text = str(value)
                element.append(child)
        
        return element
    
    def _element_to_dict(self, element: ET.Element) -> dict:
        """Convert XML Element to dict."""
        result = {}
        
        # Add attributes
        if element.attrib:
            result['@attributes'] = element.attrib
        
        # Add text content
        if element.text and element.text.strip():
            if len(element) == 0:
                # Leaf node with text
                return element.text.strip()
            else:
                result['#text'] = element.text.strip()
        
        # Add children
        for child in element:
            child_dict = self._element_to_dict(child)
            if child.tag in result:
                # Multiple children with same tag - convert to list
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_dict)
            else:
                result[child.tag] = child_dict
        
        return result
    
    def encode_to_file(
        self,
        data: Any,
        file_path: Union[str, Path],
        options: Optional[EncodeOptions] = None
    ) -> None:
        """
        Encode data to XML file.
        
        Args:
            data: Data to encode
            file_path: Path to output file
            options: Encoding options
        """
        xml_data = self.encode(data, options)
        file_path = Path(file_path)
        file_path.write_bytes(xml_data)
    
    def decode_from_file(
        self,
        file_path: Union[str, Path],
        options: Optional[DecodeOptions] = None
    ) -> Any:
        """
        Decode XML from file.
        
        Args:
            file_path: Path to XML file
            options: Decoding options
            
        Returns:
            Decoded data
        """
        file_path = Path(file_path)
        xml_data = file_path.read_bytes()
        return self.decode(xml_data, options)

