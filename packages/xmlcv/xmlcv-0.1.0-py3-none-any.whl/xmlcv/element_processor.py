"""
Dynamic element processor that analyzes XML structure and processes elements
"""

import xml.etree.ElementTree as ET
from typing import Optional, Dict, Callable, List, Any
from html import escape
from collections import defaultdict


def get_text(element: Optional[ET.Element]) -> str:
    """Safely get text from an Element, handling None."""
    if element is None:
        return ""
    
    text_parts = []
    if element.text:
        text_parts.append(element.text.strip())
    
    for child in element:
        if child.text:
            text_parts.append(child.text.strip())
        if child.tail:
            text_parts.append(child.tail.strip())
    
    return " ".join(text_parts)


def escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return escape(text)


class ElementProcessor:
    """Dynamic processor that analyzes XML structure and processes elements"""
    
    def __init__(self, config=None):
        self.config = config
        self.processors = {}
        self.element_stats = defaultdict(int)
        
    def analyze_xml_structure(self, root: ET.Element) -> Dict[str, Any]:
        """
        Analyze XML structure to understand element hierarchy and relationships
        
        Returns:
            Dictionary with structure information
        """
        structure = {
            'elements': set(),
            'hierarchy': defaultdict(set),
            'attributes': defaultdict(set),
            'text_elements': set(),
            'container_elements': set(),
        }
        
        def traverse(elem: ET.Element, parent_tag: Optional[str] = None):
            tag = self._clean_tag(elem.tag)
            structure['elements'].add(tag)
            
            if parent_tag:
                structure['hierarchy'][parent_tag].add(tag)
            
            # Collect attributes
            for attr, value in elem.attrib.items():
                structure['attributes'][tag].add(attr)
            
            # Check if element has text content
            if elem.text and elem.text.strip():
                structure['text_elements'].add(tag)
            
            # Check if element has children
            if len(elem) > 0:
                structure['container_elements'].add(tag)
                for child in elem:
                    traverse(child, tag)
        
        traverse(root)
        return structure
    
    def _clean_tag(self, tag: str) -> str:
        """Remove namespace from tag"""
        if self.config and self.config.strip_namespace:
            if '}' in tag:
                return tag.split('}')[1]
        return tag
    
    def register_processor(self, element_name: str, processor: Callable):
        """Register a custom processor for a specific element"""
        self.processors[element_name] = processor
    
    def get_processor(self, element_name: str) -> Callable:
        """Get processor for element, with fallback to default"""
        if element_name in self.processors:
            return self.processors[element_name]
        return self._default_processor
    
    def _default_processor(self, element: ET.Element, context: Dict = None) -> str:
        """Default processor for unknown elements"""
        tag = self._clean_tag(element.tag)
        text = get_text(element)
        
        # Determine HTML tag based on element name patterns
        if 'Title' in tag or 'Caption' in tag:
            return f'<div class="{tag.lower()}">{escape_html(text)}</div>'
        elif 'Sentence' in tag or 'Text' in tag:
            return f'<span class="{tag.lower()}">{escape_html(text)}</span>'
        elif 'Item' in tag or 'List' in tag:
            return f'<li class="{tag.lower()}">{escape_html(text)}</li>'
        elif 'Table' in tag:
            return self._process_table_like(element)
        else:
            # Generic container
            content = self.process_children(element, context)
            return f'<div class="{tag.lower()}">{content}</div>'
    
    def _process_table_like(self, element: ET.Element) -> str:
        """Process table-like structures"""
        html = '<table class="table">'
        for row in element.findall('.//*[Row]') or element.findall('*'):
            html += '<tr>'
            for col in row.findall('.//*[Column]') or row.findall('*'):
                text = get_text(col)
                html += f'<td>{escape_html(text)}</td>'
            html += '</tr>'
        html += '</table>'
        return html
    
    def process_children(self, element: ET.Element, context: Dict = None) -> str:
        """Process all children of an element"""
        if context is None:
            context = {}
        
        html_parts = []
        for child in element:
            processor = self.get_processor(self._clean_tag(child.tag))
            html_parts.append(processor(child, context))
        
        return ''.join(html_parts)
    
    def process_element(self, element: ET.Element, context: Dict = None) -> str:
        """Process a single element"""
        if context is None:
            context = {}
        
        tag = self._clean_tag(element.tag)
        self.element_stats[tag] += 1
        
        processor = self.get_processor(tag)
        return processor(element, context)


def get_default_processors() -> Dict[str, Callable]:
    """Get default processors for common XML elements"""
    from .processors import get_all_processors
    return get_all_processors()

