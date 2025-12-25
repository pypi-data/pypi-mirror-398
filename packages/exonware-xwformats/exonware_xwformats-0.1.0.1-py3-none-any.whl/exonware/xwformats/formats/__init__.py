#!/usr/bin/env python3
#exonware/xwformats/src/exonware/xwformats/formats/__init__.py
"""
Enterprise serialization formats.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 02-Nov-2025
"""

# Import all format categories
from . import schema
from . import database
from . import binary
from . import text
# Scientific formats not imported here to avoid scipy/numpy issues in some environments
# They can be imported explicitly: from exonware.xwformats.formats import scientific

# Re-export all serializers
from .schema import *
from .database import *
from .binary import *
from .text import *

__all__ = [
    # Module references
    'schema',
    'database',
    'binary',
    'text',
]

# Extend __all__ with all serializers
__all__.extend(schema.__all__)
__all__.extend(database.__all__)
__all__.extend(binary.__all__)
__all__.extend(text.__all__)
