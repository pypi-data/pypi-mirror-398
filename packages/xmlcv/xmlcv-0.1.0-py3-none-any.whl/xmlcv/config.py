"""
Configuration for XML to HTML converter
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from pathlib import Path


@dataclass
class ConverterConfig:
    """Configuration for XML to HTML conversion"""
    
    # Output settings
    output_dir: Optional[Path] = None
    create_index: bool = True
    convert_to_pdf: bool = False
    
    # HTML styling
    css_file: Optional[Path] = None
    custom_css: Optional[str] = None
    
    # Element mapping (can be customized)
    element_processors: Dict[str, Callable] = field(default_factory=dict)
    
    # Namespace handling
    namespace: Optional[str] = None
    strip_namespace: bool = True
    
    # Processing options
    include_toc: bool = True
    include_navigation: bool = True
    include_back_link: bool = False
    back_link_url: str = "index.html"
    
    # PDF settings
    pdf_options: Dict = field(default_factory=lambda: {
        'page-size': 'A4',
        'margin-top': '2cm',
        'margin-right': '2cm',
        'margin-bottom': '2cm',
        'margin-left': '2cm',
        'encoding': "UTF-8",
    })
    
    def __post_init__(self):
        """Initialize default element processors if not provided"""
        if not self.element_processors:
            from .element_processor import get_default_processors
            self.element_processors = get_default_processors()

