#!/usr/bin/env python3
#exonware/xwformats/src/exonware/xwformats/formats/text/__init__.py
"""
Enterprise text serialization formats.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 15-Nov-2025

Text formats: CSV, YAML, TOML, XML
"""

try:
    from .csv import XWCsvSerializer
    CSV_AVAILABLE = True
except ImportError:
    CSV_AVAILABLE = False
    XWCsvSerializer = None

try:
    from .yaml import XWYamlSerializer
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    XWYamlSerializer = None

try:
    from .toml import XWTomlSerializer
    TOML_AVAILABLE = True
except ImportError:
    TOML_AVAILABLE = False
    XWTomlSerializer = None

try:
    from .xml import XWXmlSerializer
    XML_AVAILABLE = True
except ImportError:
    XML_AVAILABLE = False
    XWXmlSerializer = None

__all__ = []

if CSV_AVAILABLE:
    __all__.append("XWCsvSerializer")
if YAML_AVAILABLE:
    __all__.append("XWYamlSerializer")
if TOML_AVAILABLE:
    __all__.append("XWTomlSerializer")
if XML_AVAILABLE:
    __all__.append("XWXmlSerializer")


