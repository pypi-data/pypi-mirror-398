"""
Main XML to HTML Converter class with dynamic element processing
"""

import os
import xml.etree.ElementTree as ET
from pathlib import Path
from html import escape
from typing import Optional, Dict, List
import json

# PDF libraries will be imported lazily when needed
WEASYPRINT_AVAILABLE = None
PDFKIT_AVAILABLE = None

def _check_weasyprint():
    """Lazy check for weasyprint availability"""
    global WEASYPRINT_AVAILABLE
    if WEASYPRINT_AVAILABLE is None:
        try:
            from weasyprint import HTML, CSS
            WEASYPRINT_AVAILABLE = True
        except (ImportError, OSError):
            WEASYPRINT_AVAILABLE = False
    return WEASYPRINT_AVAILABLE

def _check_pdfkit():
    """Lazy check for pdfkit availability"""
    global PDFKIT_AVAILABLE
    if PDFKIT_AVAILABLE is None:
        try:
            import pdfkit
            PDFKIT_AVAILABLE = True
        except ImportError:
            PDFKIT_AVAILABLE = False
    return PDFKIT_AVAILABLE

from .element_processor import ElementProcessor, get_text, escape_html
from .config import ConverterConfig
from .processors import get_all_processors

# Import XMLConverter for backward compatibility and new plugin system
from .converter_v2 import XMLConverter


class XMLToHTMLConverter:
    """
    Flexible XML to HTML converter that dynamically handles various XML structures
    by analyzing the XML schema and generating appropriate HTML output.
    """
    
    HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        {css}
    </style>
</head>
<body>
    <div class="container">
        {back_link}
        <div class="header">
            <div class="document-title">{document_title}</div>
            <div class="document-meta">{document_meta}</div>
        </div>
        {enact_statement}
        {toc}
        {content}
    </div>
    {navigation}
</body>
</html>
"""
    
    def __init__(self, config: Optional[ConverterConfig] = None):
        """
        Initialize converter with configuration
        
        Args:
            config: ConverterConfig instance, or None for default config
        """
        self.config = config or ConverterConfig()
        self.processor = ElementProcessor(self.config)
        
        # Register default processors
        default_processors = get_all_processors()
        for element_name, processor_func in default_processors.items():
            self.processor.register_processor(element_name, processor_func)
        
        # Register custom processors from config
        for element_name, processor_func in self.config.element_processors.items():
            self.processor.register_processor(element_name, processor_func)
    
    def analyze_xml(self, xml_path: Path) -> Dict:
        """
        Analyze XML structure to understand its schema
        
        Args:
            xml_path: Path to XML file
            
        Returns:
            Dictionary with structure information
        """
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            return self.processor.analyze_xml_structure(root)
        except Exception as e:
            return {'error': str(e)}
    
    def convert_file(
        self,
        xml_path: Path,
        output_path: Optional[Path] = None,
        convert_to_pdf: Optional[bool] = None
    ) -> str:
        """
        Convert a single XML file to HTML
        
        Args:
            xml_path: Path to XML file
            output_path: Optional output path for HTML file
            convert_to_pdf: Whether to also convert to PDF (overrides config)
            
        Returns:
            HTML content as string
        """
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
        except ET.ParseError as e:
            return f"<html><body><h1>Error parsing XML</h1><p>{escape(str(e))}</p></body></html>"
        
        # Fully dynamic processing - no hardcoded XML structure assumptions
        # Extract title dynamically - handle namespaces properly
        title_elem = None
        title_text = None
        
        # Method 1: Iterate through all elements to find title-like elements (handles namespaces)
        for elem in root.iter():
            tag = self.processor._clean_tag(elem.tag)
            if tag.lower() in ['title', 'name', 'heading', 'documenttitle', 'book_title', 'document_title']:
                text = get_text(elem).strip()
                if text and len(text) > 0 and len(text) < 500:
                    if text.lower() not in ['title', 'name', 'heading']:
                        title_elem = elem
                        title_text = text
                        break
        
        # Method 2: If no title found, try common patterns
        if not title_text:
            title_patterns = [
                './/title', './/Title', './/DocumentTitle',
                './/book_title', './/document_title', './/doc_title',
                './/name', './/Name', 
                './/heading', './/Heading'
            ]
            for pattern in title_patterns:
                found_elems = root.findall(pattern)
                if found_elems:
                    for elem in found_elems:
                        text = get_text(elem).strip()
                        if text and len(text) > 0 and len(text) < 500:
                            title_elem = elem
                            title_text = text
                            break
                    if title_text:
                        break
        
        # Method 3: Look for titles in common document structures
        if not title_text:
            for container_tag in ['book', 'document', 'article', 'chapter', 'section']:
                for elem in root.iter():
                    tag = self.processor._clean_tag(elem.tag)
                    if tag.lower() == container_tag:
                        for child in elem.iter():
                            child_tag = self.processor._clean_tag(child.tag)
                            if child_tag.lower() in ['title', 'name']:
                                text = get_text(child).strip()
                                if text and len(text) > 0 and len(text) < 500:
                                    title_elem = child
                                    title_text = text
                                    break
                        if title_text:
                            break
                if title_text:
                    break
        
        # Final fallback: use root tag name
        if not title_text:
            root_tag = self.processor._clean_tag(root.tag)
            title_text = root_tag.replace('_', ' ').replace('-', ' ').title()
        
        document_title = title_text
        
        # Extract metadata from root attributes
        document_meta = ""
        if root.attrib:
            meta_parts = []
            for key, value in root.attrib.items():
                clean_key = key.split('}')[-1] if '}' in key else key
                if len(str(value)) < 100:
                    meta_parts.append(f"{clean_key}: {value}")
            if meta_parts:
                document_meta = " | ".join(meta_parts)
        
        # Process entire XML tree using ElementProcessor (fully dynamic)
        context = {'processor': self.processor}
        content_html = self.processor.process_element(root, context)
        
        # Extract TOC if exists (check for common TOC patterns)
        toc_html = ""
        if self.config.include_toc:
            toc_patterns = ['.//TOC', './/toc', './/table_of_contents', './/contents']
            for pattern in toc_patterns:
                toc_elem = root.find(pattern)
                if toc_elem is not None:
                    toc_processor = self.processor.get_processor(self.processor._clean_tag(toc_elem.tag))
                    toc_html = toc_processor(toc_elem, context)
                    break
            else:
                # Generate a simple TOC from headings if no explicit TOC element
                generated_toc_items = self._generate_toc_from_headings(root)
                if generated_toc_items:
                    toc_html = f'''
                    <div class="toc">
                        <div class="toc-title">Contents</div>
                        <ul>{"".join(generated_toc_items)}</ul>
                    </div>
                    '''
        
        # No hardcoded enact_statement - let ElementProcessor handle it if it exists
        enact_statement_html = ""
        
        # Build navigation
        navigation_html = ""
        if self.config.include_navigation:
            navigation_items = self._extract_navigation_items(root)
            if navigation_items:
                navigation_html = f'''
                <div class="navigation">
                    <div style="font-weight: bold; margin-bottom: 10px; color: #2c3e50;">Contents</div>
                    {"".join(navigation_items)}
                </div>
                '''
        
        back_link_html = ""
        if self.config.include_back_link:
            back_link_html = f'<a href="{self.config.back_link_url}" class="back-link">← Back to Index</a>'
        
        # Get CSS
        css = self._get_css()
        
        # Format metadata HTML
        document_meta_html = ""
        if document_meta:
            document_meta_html = f'<div class="document-meta">{escape_html(document_meta)}</div>'
        
        # Build final HTML
        final_html = self.HTML_TEMPLATE.format(
            title=escape_html(document_title),
            css=css,
            document_title=escape_html(document_title),
            document_meta=document_meta_html,
            enact_statement=enact_statement_html,
            toc=toc_html,
            content=content_html,
            navigation=navigation_html,
            back_link=back_link_html
        )
        
        # Write to file if output path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(final_html)
            
            # Convert to PDF if requested
            if convert_to_pdf is None:
                convert_to_pdf = self.config.convert_to_pdf
            
            if convert_to_pdf:
                pdf_path = output_path.with_suffix('.pdf')
                if self._html_to_pdf(output_path, pdf_path):
                    print(f"✅ PDF created: {pdf_path}")
                else:
                    print(f"❌ Failed to create PDF for {output_path.name}")
        
        return final_html
    
    def _generate_toc_from_headings(self, root: ET.Element) -> List[str]:
        """Generate a simple TOC from heading elements found in the processed content."""
        toc_items = []
        # This would require parsing the generated HTML, which is complex.
        # For now, we'll rely on explicit TOC elements or a simpler approach.
        # A more robust solution would involve a second pass after HTML generation.
        return toc_items
    
    def _extract_navigation_items(self, root: ET.Element) -> List[str]:
        """Extract navigation items from XML dynamically"""
        items = []
        
        # Dynamic navigation extraction - look for common structural elements
        nav_patterns = [
            ('.//Chapter', 'ChapterTitle', 'Num', 'chapter'),
            ('.//Section', 'SectionTitle', 'Num', 'section'),
            ('.//Article', 'ArticleTitle', 'Num', 'article'),
            ('.//Part', 'PartTitle', 'Num', 'part'),
            ('.//chapter', 'title', 'id', 'chapter'),
            ('.//section', 'title', 'id', 'section'),
            ('.//article', 'title', 'id', 'article'),
        ]
        
        for pattern, title_attr, id_attr, nav_type in nav_patterns:
            elements = root.findall(pattern)
            if elements:
                for elem in elements:
                    # Try to find title
                    title_elem = elem.find(title_attr) if title_attr else None
                    if title_elem is None:
                        # Try common title patterns
                        for title_pattern in ['.//title', './/Title', './/name', './/Name']:
                            title_elem = elem.find(title_pattern)
                            if title_elem is not None:
                                break
                    
                    title = get_text(title_elem) if title_elem is not None else ""
                    if not title:
                        # Use element text if no title element
                        title = get_text(elem)
                    
                    # Get ID/Num
                    elem_id = elem.get(id_attr, '') if id_attr else elem.get('id', elem.get('Num', ''))
                    
                    if title and title.strip():
                        items.append(
                            f'<a href="#{nav_type}-{elem_id}" class="nav-link">{escape_html(title.strip())}</a>'
                        )
        
        return items
    
    def _get_css(self) -> str:
        """Get CSS styles"""
        if self.config.custom_css:
            return self.config.custom_css
        
        if self.config.css_file and self.config.css_file.exists():
            with open(self.config.css_file, 'r', encoding='utf-8') as f:
                return f.read()
        
        # Return default CSS
        return self._get_default_css()
    
    def _get_default_css(self) -> str:
        """Get default CSS styles"""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.8;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-radius: 8px;
        }
        .header {
            border-bottom: 3px solid #2c3e50;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        .document-title {
            font-size: 2em;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }
        .document-meta {
            color: #666;
            font-size: 0.9em;
            margin-bottom: 5px;
        }
        .toc {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin: 30px 0;
        }
        .toc-title {
            font-size: 1.3em;
            font-weight: bold;
            margin-bottom: 15px;
            color: #2c3e50;
        }
        .toc-chapter {
            margin: 10px 0;
            padding-left: 20px;
        }
        .toc-section {
            margin: 5px 0;
            padding-left: 40px;
            color: #555;
        }
        .chapter {
            margin: 40px 0;
            border-top: 2px solid #e0e0e0;
            padding-top: 20px;
        }
        .chapter-title {
            font-size: 1.5em;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 20px;
        }
        .article {
            margin: 30px 0;
            padding: 20px;
            background: #fafafa;
            border-left: 4px solid #3498db;
            border-radius: 4px;
        }
        .article-title {
            font-size: 1.2em;
            font-weight: bold;
            color: #2980b9;
            margin-bottom: 10px;
        }
        .article-caption {
            font-size: 0.9em;
            color: #7f8c8d;
            margin-bottom: 5px;
            font-style: italic;
        }
        .paragraph {
            margin: 15px 0;
            padding-left: 20px;
        }
        .paragraph-num {
            font-weight: bold;
            color: #34495e;
            margin-right: 10px;
        }
        .sentence {
            margin: 10px 0;
            text-indent: 1em;
        }
        ruby {
            ruby-align: center;
        }
        rt {
            font-size: 0.7em;
            line-height: 1;
        }
        .item {
            margin: 10px 0;
            padding-left: 30px;
        }
        .item-title {
            font-weight: bold;
            color: #27ae60;
            margin-right: 10px;
        }
        .section {
            margin: 30px 0;
            padding-left: 20px;
        }
        .section-title {
            font-size: 1.3em;
            font-weight: bold;
            color: #8e44ad;
            margin-bottom: 15px;
        }
        .table-wrapper {
            margin: 20px 0;
            overflow-x: auto;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            border: 1px solid #ddd;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            vertical-align: top;
        }
        th {
            background-color: #f2f2f2;
            font-weight: bold;
        }
        .navigation {
            position: fixed;
            top: 20px;
            right: 20px;
            background: white;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            max-width: 300px;
            max-height: 80vh;
            overflow-y: auto;
        }
        .nav-link {
            display: block;
            padding: 5px 10px;
            color: #3498db;
            text-decoration: none;
            border-radius: 3px;
            margin: 2px 0;
        }
        .nav-link:hover {
            background: #ecf0f1;
        }
        .back-link {
            display: inline-block;
            margin-bottom: 20px;
            padding: 10px 20px;
            background: #3498db;
            color: white;
            text-decoration: none;
            border-radius: 5px;
        }
        .back-link:hover {
            background: #2980b9;
        }
        @media print {
            .navigation {
                display: none;
            }
            body {
                background: white;
                padding: 0;
            }
            .container {
                box-shadow: none;
                padding: 20px;
            }
        }
        @page {
            size: A4;
            margin: 2cm;
        }
        """
    
    def _html_to_pdf(self, html_path: Path, pdf_path: Path) -> bool:
        """Convert HTML to PDF"""
        try:
            if _check_weasyprint():
                from weasyprint import HTML
                HTML(filename=str(html_path)).write_pdf(str(pdf_path))
                return True
            elif _check_pdfkit():
                import pdfkit
                pdfkit.from_file(
                    str(html_path),
                    str(pdf_path),
                    options=self.config.pdf_options
                )
                return True
            else:
                print("⚠️  No PDF library available. Install weasyprint or pdfkit")
                return False
        except Exception as e:
            print(f"❌ Error converting to PDF: {e}")
            return False
    
    def convert_directory(
        self,
        input_dir: Path,
        output_dir: Optional[Path] = None,
        create_index: Optional[bool] = None
    ) -> Dict[str, str]:
        """
        Convert all XML files in a directory
        
        Args:
            input_dir: Directory containing XML files
            output_dir: Output directory (default: input_dir/html)
            create_index: Whether to create index page (default: from config)
            
        Returns:
            Dictionary mapping XML paths to HTML paths
        """
        if output_dir is None:
            output_dir = input_dir.parent / "html"
        
        if create_index is None:
            create_index = self.config.create_index
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        xml_files = list(input_dir.rglob("*.xml"))
        converted = {}
        
        print(f"Found {len(xml_files)} XML files")
        
        for xml_file in xml_files:
            rel_path = xml_file.relative_to(input_dir)
            html_path = output_dir / rel_path.with_suffix('.html')
            
            try:
                self.convert_file(xml_file, html_path)
                converted[str(xml_file)] = str(html_path)
                print(f"✅ Converted: {xml_file.name} -> {html_path.name}")
            except Exception as e:
                print(f"❌ Error converting {xml_file.name}: {e}")
        
        if create_index:
            self._create_index_page(converted, output_dir)
        
        print(f"\n✅ Converted {len(converted)} files to HTML")
        return converted
    
    def _create_index_page(self, converted_files: Dict[str, str], output_dir: Path):
        """Create index page listing all converted files"""
        # Implementation for index page creation
        pass

