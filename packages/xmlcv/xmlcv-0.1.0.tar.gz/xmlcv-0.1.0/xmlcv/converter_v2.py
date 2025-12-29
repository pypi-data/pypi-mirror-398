"""
Main XML Converter class with plugin system support
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, Dict, List
from .element_processor import ElementProcessor
from .config import ConverterConfig
from .plugins import PluginRegistry, OutputPlugin


class XMLConverter:
    """
    Main converter class that uses plugins for different output formats
    """
    
    def __init__(self, config: Optional[ConverterConfig] = None):
        """
        Initialize converter with configuration
        
        Args:
            config: ConverterConfig instance, or None for default config
        """
        self.config = config or ConverterConfig()
        self.processor = ElementProcessor(self.config)
        self.plugin_registry = PluginRegistry()
        
        # Register default plugins
        from .plugins import HTMLPlugin, PDFPlugin, DOCXPlugin, PPTXPlugin, MarkdownPlugin
        self.plugin_registry.register("html", HTMLPlugin)
        self.plugin_registry.register("pdf", PDFPlugin)
        self.plugin_registry.register("docx", DOCXPlugin)
        self.plugin_registry.register("pptx", PPTXPlugin)
        self.plugin_registry.register("markdown", MarkdownPlugin)
    
    def list_plugins(self) -> List:
        """List all available plugins"""
        return self.plugin_registry.list_plugins()
    
    def convert(
        self,
        xml_path: Path,
        output_path: Optional[Path] = None,
        output_format: str = "html",
        **kwargs
    ) -> bool:
        """
        Convert XML file to specified output format
        
        Args:
            xml_path: Path to XML file
            output_path: Output file path (auto-determined if None)
            output_format: Output format (html, pdf, etc.)
            **kwargs: Additional format-specific options
            
        Returns:
            True if successful
        """
        # Determine output path if not provided
        if output_path is None:
            if output_format == "html":
                output_path = xml_path.with_suffix('.html')
            elif output_format == "pdf":
                output_path = xml_path.with_suffix('.pdf')
            else:
                # Try to get extension from plugin
                plugin = self.plugin_registry.get_plugin(output_format)
                if plugin and plugin.info.file_extensions:
                    ext = plugin.info.file_extensions[0]
                    output_path = xml_path.with_suffix(ext)
                else:
                    output_path = xml_path.with_suffix(f'.{output_format}')
        
        # Get plugin
        plugin = self.plugin_registry.get_plugin(output_format, self.config.__dict__)
        if plugin is None:
            print(f"❌ Unknown output format: {output_format}")
            print(f"Available formats: {', '.join(self.plugin_registry.get_available_plugins())}")
            return False
        
        # Check if plugin is available
        available, error = plugin.check_dependencies()
        if not available:
            print(f"❌ Plugin '{output_format}' is not available: {error}")
            return False
        
        # Prepare intermediate data
        intermediate_data = {
            'config': self.config.__dict__,
            **kwargs
        }
        
        # Convert
        return plugin.convert(xml_path, output_path, intermediate_data)
    
    def convert_to_multiple_formats(
        self,
        xml_path: Path,
        output_formats: List[str],
        output_dir: Optional[Path] = None
    ) -> Dict[str, bool]:
        """
        Convert XML to multiple output formats
        
        Args:
            xml_path: Path to XML file
            output_formats: List of output formats (e.g., ['html', 'pdf'])
            output_dir: Output directory (default: same as XML file)
            
        Returns:
            Dictionary mapping format to success status
        """
        if output_dir is None:
            output_dir = xml_path.parent
        
        results = {}
        intermediate_data = {'config': self.config.__dict__}
        
        for fmt in output_formats:
            plugin = self.plugin_registry.get_plugin(fmt, self.config.__dict__)
            if plugin is None:
                results[fmt] = False
                continue
            
            available, error = plugin.check_dependencies()
            if not available:
                print(f"⚠️  Skipping {fmt}: {error}")
                results[fmt] = False
                continue
            
            # Determine output path
            if plugin.info.file_extensions:
                ext = plugin.info.file_extensions[0]
            else:
                ext = f'.{fmt}'
            
            output_path = output_dir / xml_path.with_suffix(ext).name
            
            success = plugin.convert(xml_path, output_path, intermediate_data)
            results[fmt] = success
        
        return results

