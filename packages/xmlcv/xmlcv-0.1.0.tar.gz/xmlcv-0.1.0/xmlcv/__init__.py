"""
XMLCV - XML to Document Converter

A flexible converter that dynamically handles various XML structures
by analyzing the XML schema and generating appropriate output formats.
"""

from .converter import XMLToHTMLConverter, XMLConverter
from .element_processor import ElementProcessor
from .config import ConverterConfig
from .plugins import PluginRegistry, OutputPlugin

__version__ = "0.1.0"
__all__ = [
    "XMLToHTMLConverter",
    "XMLConverter",
    "ElementProcessor",
    "ConverterConfig",
    "PluginRegistry",
    "OutputPlugin"
]

