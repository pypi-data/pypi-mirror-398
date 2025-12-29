"""
HTML output plugin
"""

from pathlib import Path
from typing import Dict, Optional
from .base import OutputPlugin, PluginInfo


class HTMLPlugin(OutputPlugin):
    """Plugin for HTML output format"""
    
    def get_info(self) -> PluginInfo:
        return PluginInfo(
            name="html",
            description="Convert XML to HTML with styling and navigation",
            version="0.1.0",
            dependencies=[],
            file_extensions=[".html", ".htm"]
        )
    
    def check_dependencies(self) -> tuple[bool, Optional[str]]:
        """HTML plugin has no external dependencies"""
        return True, None
    
    def convert(
        self,
        xml_path: Path,
        output_path: Path,
        intermediate_data: Optional[Dict] = None
    ) -> bool:
        """
        Convert XML to HTML
        
        Args:
            xml_path: Path to XML file
            output_path: Path for HTML output
            intermediate_data: Optional data from other plugins
            
        Returns:
            True if successful
        """
        from ..converter import XMLToHTMLConverter
        from ..config import ConverterConfig
        
        # Use config from intermediate_data if available
        config_dict = intermediate_data.get('config', {}) if intermediate_data else {}
        config = ConverterConfig(**config_dict)
        
        converter = XMLToHTMLConverter(config)
        
        try:
            converter.convert_file(xml_path, output_path, convert_to_pdf=False)
            return True
        except Exception as e:
            print(f"❌ Error converting to HTML: {e}")
            return False

