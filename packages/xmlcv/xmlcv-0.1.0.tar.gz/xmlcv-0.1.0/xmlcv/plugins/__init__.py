"""
Plugin system for output formats
"""

from .base import OutputPlugin, PluginRegistry
from .html_plugin import HTMLPlugin
from .pdf_plugin import PDFPlugin
from .docx_plugin import DOCXPlugin
from .pptx_plugin import PPTXPlugin
from .markdown_plugin import MarkdownPlugin

__all__ = [
    "OutputPlugin",
    "PluginRegistry",
    "HTMLPlugin",
    "PDFPlugin",
    "DOCXPlugin",
    "PPTXPlugin",
    "MarkdownPlugin"
]

# Register default plugins
registry = PluginRegistry()
registry.register("html", HTMLPlugin)
registry.register("pdf", PDFPlugin)
registry.register("docx", DOCXPlugin)
registry.register("pptx", PPTXPlugin)
registry.register("markdown", MarkdownPlugin)

