"""
Markdown output plugin
"""

from pathlib import Path
from typing import Dict, Optional
from .base import OutputPlugin, PluginInfo


class MarkdownPlugin(OutputPlugin):
    """Plugin for Markdown output format"""
    
    def get_info(self) -> PluginInfo:
        return PluginInfo(
            name="markdown",
            description="Convert XML to Markdown format",
            version="0.1.0",
            dependencies=["markdown"],
            file_extensions=[".md", ".markdown"]
        )
    
    def check_dependencies(self) -> tuple[bool, Optional[str]]:
        """Check if Markdown dependencies are available"""
        # Markdown plugin doesn't actually need markdown library for basic conversion
        # But we can use it for advanced features
        return True, None
    
    def convert(
        self,
        xml_path: Path,
        output_path: Path,
        intermediate_data: Optional[Dict] = None
    ) -> bool:
        """
        Convert XML to Markdown
        
        Args:
            xml_path: Path to XML file
            output_path: Path for Markdown output
            intermediate_data: Optional data from other plugins
            
        Returns:
            True if successful
        """
        # Import the MD converter (we'll create this or use existing)
        try:
            # For now, use the existing xml_to_md_converter if available
            # In the future, this can be refactored to use the plugin system
            import sys
            import os
            parent_dir = Path(__file__).parent.parent.parent.parent
            md_converter_path = parent_dir / "xml_to_md_converter.py"
            
            if md_converter_path.exists():
                import importlib.util
                spec = importlib.util.spec_from_file_location("xml_to_md_converter", md_converter_path)
                md_converter = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(md_converter)
                
                md_converter.xml_to_md(xml_path, output_path)
                return True
            else:
                print("⚠️  Markdown converter not found. Using basic conversion.")
                return False
        except Exception as e:
            print(f"❌ Error converting to Markdown: {e}")
            return False

