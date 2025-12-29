"""
PDF output plugin
"""

from pathlib import Path
from typing import Dict, Optional
from .base import OutputPlugin, PluginInfo


class PDFPlugin(OutputPlugin):
    """Plugin for PDF output format"""
    
    def get_info(self) -> PluginInfo:
        return PluginInfo(
            name="pdf",
            description="Convert XML to PDF (requires HTML as intermediate step)",
            version="0.1.0",
            dependencies=["weasyprint", "pdfkit"],
            file_extensions=[".pdf"]
        )
    
    def check_dependencies(self) -> tuple[bool, Optional[str]]:
        """Check if PDF dependencies are available"""
        # Try weasyprint first
        try:
            from weasyprint import HTML
            return True, None
        except ImportError:
            pass
        
        # Try pdfkit
        try:
            import pdfkit
            return True, None
        except ImportError:
            pass
        
        return False, "Neither weasyprint nor pdfkit is installed. Install with: pip install 'xmlcv[pdf]'"
    
    def convert(
        self,
        xml_path: Path,
        output_path: Path,
        intermediate_data: Optional[Dict] = None
    ) -> bool:
        """
        Convert XML to PDF (via HTML intermediate)
        
        Args:
            xml_path: Path to XML file
            output_path: Path for PDF output
            intermediate_data: Optional data from other plugins (should contain HTML)
            
        Returns:
            True if successful
        """
        from ..converter import XMLToHTMLConverter
        from ..config import ConverterConfig
        
        # Check dependencies
        available, error = self.check_dependencies()
        if not available:
            print(f"❌ {error}")
            return False
        
        # Use config from intermediate_data if available
        config_dict = intermediate_data.get('config', {}) if intermediate_data else {}
        config = ConverterConfig(**config_dict)
        
        converter = XMLToHTMLConverter(config)
        
        # First convert to HTML (temporary)
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp_html:
            tmp_html_path = Path(tmp_html.name)
        
        try:
            # Convert to HTML first
            converter.convert_file(xml_path, tmp_html_path, convert_to_pdf=False)
            
            # Then convert HTML to PDF
            if converter._html_to_pdf(tmp_html_path, output_path):
                # Clean up temp file
                tmp_html_path.unlink()
                return True
            else:
                return False
        except Exception as e:
            print(f"❌ Error converting to PDF: {e}")
            if tmp_html_path.exists():
                tmp_html_path.unlink()
            return False

