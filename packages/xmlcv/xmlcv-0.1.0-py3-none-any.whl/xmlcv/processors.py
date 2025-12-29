"""
Element processors for XML elements
These functions process specific XML elements into HTML
"""

import xml.etree.ElementTree as ET
from typing import Optional, Dict, Callable
from html import escape

from .element_processor import get_text, escape_html


def process_document(element: ET.Element, context: Dict = None) -> str:
    """Process Document root element by processing its children"""
    processor = context.get('processor')
    if processor:
        return processor.process_children(element, context)
    return ""

def process_document_title(element: ET.Element, context: Dict = None) -> str:
    """Process DocumentTitle element"""
    text = get_text(element)
    return f'<div class="document-title">{escape_html(text)}</div>' if text else ""


def process_enact_statement(element: ET.Element, context: Dict = None) -> str:
    """Process EnactStatement element"""
    text = get_text(element)
    if not text:
        return ""
    return f'<div class="enact-statement" style="background: #fff3cd; padding: 20px; border-left: 4px solid #ffc107; margin: 20px 0; border-radius: 4px;"><p style="margin: 0; line-height: 1.8;">{escape_html(text)}</p></div>'


def process_toc(element: ET.Element, context: Dict = None) -> str:
    """Process TOC (Table of Contents) element"""
    toc_label = get_text(element.find('TOCLabel'))
    
    html = '<div class="toc" style="background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 30px 0;">'
    if toc_label:
        html += f'<div class="toc-title" style="font-size: 1.3em; font-weight: bold; margin-bottom: 15px; color: #2c3e50;">{escape_html(toc_label)}</div>'
    
    # Process TOC chapters
    for chapter in element.findall('.//TOCChapter'):
        chapter_title = get_text(chapter.find('ChapterTitle'))
        chapter_num = chapter.get('Num', '')
        article_range = get_text(chapter.find('ArticleRange'))
        
        html += f'<div class="toc-chapter" style="margin: 10px 0; padding-left: 20px;">'
        html += f'<a href="#chapter-{chapter_num}" class="nav-link">{escape_html(chapter_title)}</a>'
        if article_range:
            html += f' <span style="color: #666;">{escape_html(article_range)}</span>'
        html += '</div>'
        
        # Process sections
        for section in chapter.findall('TOCSection'):
            section_title = get_text(section.find('SectionTitle'))
            section_num = section.get('Num', '')
            section_range = get_text(section.find('ArticleRange'))
            
            html += f'<div class="toc-section" style="margin: 5px 0; padding-left: 40px; color: #555;">'
            html += f'<a href="#section-{section_num}" class="nav-link">{escape_html(section_title)}</a>'
            if section_range:
                html += f' <span style="color: #666;">{escape_html(section_range)}</span>'
            html += '</div>'
    
    # Process supplementary provisions
    suppl = element.find('TOCSupplProvision')
    if suppl is not None:
        suppl_label = get_text(suppl.find('SupplProvisionLabel'))
        if suppl_label:
            html += f'<div class="toc-chapter"><strong>{escape_html(suppl_label)}</strong></div>'
    
    html += '</div>'
    return html


def process_chapter(element: ET.Element, context: Dict = None) -> str:
    """Process Chapter element"""
    chapter_title = get_text(element.find('ChapterTitle'))
    chapter_num = element.get('Num', '')
    
    processor = context.get('processor') if context else None
    
    sections_html = ""
    articles_html = ""
    
    # Process sections
    for section in element.findall('Section'):
        if processor:
            sections_html += processor.process_element(section, context)
        else:
            sections_html += process_section(section, context)
    
    # Process articles directly under chapter
    for article in element.findall('Article'):
        if processor:
            articles_html += processor.process_element(article, context)
        else:
            articles_html += process_article(article, context)
    
    html = f'<div class="chapter" id="chapter-{chapter_num}" style="margin: 40px 0; border-top: 2px solid #e0e0e0; padding-top: 20px;">'
    if chapter_title:
        html += f'<div class="chapter-title" style="font-size: 1.5em; font-weight: bold; color: #2c3e50; margin-bottom: 20px;">{escape_html(chapter_title)}</div>'
    html += sections_html
    html += articles_html
    html += '</div>'
    return html


def process_section(element: ET.Element, context: Dict = None) -> str:
    """Process Section element"""
    section_title = get_text(element.find('SectionTitle'))
    section_num = element.get('Num', '')
    
    processor = context.get('processor') if context else None
    
    subsections_html = ""
    articles_html = ""
    
    # Process subsections
    for subsection in element.findall('Subsection'):
        if processor:
            subsections_html += processor.process_element(subsection, context)
        else:
            subsections_html += process_subsection(subsection, context)
    
    # Process articles
    for article in element.findall('Article'):
        if processor:
            articles_html += processor.process_element(article, context)
        else:
            articles_html += process_article(article, context)
    
    html = f'<div class="section" id="section-{section_num}" style="margin: 30px 0; padding-left: 20px;">'
    if section_title:
        html += f'<div class="section-title" style="font-size: 1.3em; font-weight: bold; color: #8e44ad; margin-bottom: 15px;">{escape_html(section_title)}</div>'
    html += subsections_html
    html += articles_html
    html += '</div>'
    return html


def process_subsection(element: ET.Element, context: Dict = None) -> str:
    """Process Subsection element"""
    subsection_title = get_text(element.find('SubsectionTitle'))
    
    processor = context.get('processor') if context else None
    
    articles_html = ""
    for article in element.findall('Article'):
        if processor:
            articles_html += processor.process_element(article, context)
        else:
            articles_html += process_article(article, context)
    
    html = '<div class="subsection" style="margin: 20px 0; padding-left: 30px;">'
    if subsection_title:
        html += f'<div class="section-title" style="font-size: 1.1em; color: #9b59b6;">{escape_html(subsection_title)}</div>'
    html += articles_html
    html += '</div>'
    return html


def process_article(element: ET.Element, context: Dict = None) -> str:
    """Process Article element"""
    article_title = get_text(element.find('ArticleTitle'))
    article_caption = get_text(element.find('ArticleCaption'))
    article_num = element.get('Num', '')
    
    processor = context.get('processor') if context else None
    
    paragraphs_html = ""
    for paragraph in element.findall('Paragraph'):
        if processor:
            paragraphs_html += processor.process_element(paragraph, context)
        else:
            paragraphs_html += process_paragraph(paragraph, context)
    
    # Process Style/StyleStruct
    styles_html = ""
    for style_elem in element.findall('Style'):
        style_text = get_text(style_elem)
        if style_text:
            styles_html += f'<div class="style" style="margin: 10px 0; padding: 10px; background: #e8f5e9; border-left: 3px solid #4caf50; border-radius: 3px;">{escape_html(style_text)}</div>'
    
    html = f'<div class="article" id="article-{article_num}" style="margin: 30px 0; padding: 20px; background: #fafafa; border-left: 4px solid #3498db; border-radius: 4px;">'
    if article_caption:
        html += f'<div class="article-caption" style="font-size: 0.9em; color: #7f8c8d; margin-bottom: 5px; font-style: italic;">{escape_html(article_caption)}</div>'
    if article_title:
        html += f'<div class="article-title" style="font-size: 1.2em; font-weight: bold; color: #2980b9; margin-bottom: 10px;">{escape_html(article_title)}</div>'
    html += paragraphs_html
    html += styles_html
    html += '</div>'
    return html


def process_paragraph(element: ET.Element, context: Dict = None) -> str:
    """Process Paragraph element"""
    paragraph_num = get_text(element.find('ParagraphNum'))
    
    processor = context.get('processor') if context else None
    
    sentences_html = ""
    # Find sentences in ParagraphSentence containers
    for sentence in element.findall('ParagraphSentence/Sentence'):
        if processor:
            sentences_html += processor.process_element(sentence, context)
        else:
            sentences_html += process_sentence(sentence, context)
    
    # Also find sentences that are direct children of Paragraph (if any)
    for sentence in element.findall('Sentence'):
        # Skip if already processed via ParagraphSentence
        if sentence not in [s for ps in element.findall('ParagraphSentence') for s in ps.findall('Sentence')]:
            if processor:
                sentences_html += processor.process_element(sentence, context)
            else:
                sentences_html += process_sentence(sentence, context)
    
    items_html = ""
    for item in element.findall('Item'):
        if processor:
            items_html += processor.process_element(item, context)
        else:
            items_html += process_item(item, context)
    
    # Process other elements
    lists_html = ""
    for list_elem in element.findall('List'):
        for list_sentence in list_elem.findall('ListSentence/Sentence'):
            if processor:
                lists_html += f'<div class="list" style="margin: 10px 0; padding-left: 20px; list-style-type: disc;">{processor.process_element(list_sentence, context)}</div>'
            else:
                lists_html += f'<div class="list" style="margin: 10px 0; padding-left: 20px; list-style-type: disc;">{process_sentence(list_sentence, context)}</div>'
    
    tables_html = ""
    for table_struct in element.findall('TableStruct'):
        if processor:
            tables_html += processor.process_element(table_struct, context)
        else:
            tables_html += process_table_struct(table_struct, context)
    
    html = '<div class="paragraph" style="margin: 15px 0; padding-left: 20px;">'
    if paragraph_num:
        html += f'<span class="paragraph-num" style="font-weight: bold; color: #34495e; margin-right: 10px;">{escape_html(paragraph_num)}</span>'
    html += sentences_html
    html += items_html
    html += lists_html
    html += tables_html
    html += '</div>'
    return html


def process_sentence(element: ET.Element, context: Dict = None) -> str:
    """Process Sentence element with Ruby annotations"""
    ruby_elements = list(element.findall('Ruby'))
    sub_elements = list(element.findall('Sub'))
    
    if ruby_elements or sub_elements:
        html = '<span class="sentence" style="margin: 10px 0; text-indent: 1em;">'
        if element.text:
            html += escape_html(element.text)
        
        for child in element:
            if child.tag == 'Ruby':
                rt = child.find('Rt')
                if rt is not None:
                    ruby_text = child.text or ""
                    rt_text = get_text(rt)
                    html += f'<ruby>{escape_html(ruby_text)}<rt>{escape_html(rt_text)}</rt></ruby>'
            elif child.tag == 'Sub':
                sub_text = get_text(child)
                html += f'<sub>{escape_html(sub_text)}</sub>'
            
            if child.tail:
                html += escape_html(child.tail)
        
        html += '</span>'
        return html
    
    # Always render sentence, even if empty or short (1-2 characters)
    # This ensures all sentences are preserved, including table cell content
    text = get_text(element)
    # Use non-breaking space for empty sentences to maintain structure
    if not text or not text.strip():
        text = '\u00A0'  # Non-breaking space
    return f'<span class="sentence" style="margin: 10px 0; text-indent: 1em;">{escape_html(text)}</span>'


def process_item(element: ET.Element, context: Dict = None) -> str:
    """Process Item element"""
    item_title = get_text(element.find('ItemTitle'))
    
    # Check for Column elements (table-like)
    item_sentence = element.find('ItemSentence')
    if item_sentence is not None:
        columns = item_sentence.findall('Column')
        if columns:
            processor = context.get('processor') if context else None
            html = '<div class="item" style="margin: 10px 0; padding-left: 30px;">'
            if item_title:
                html += f'<span class="item-title" style="font-weight: bold; color: #27ae60; margin-right: 10px;">{escape_html(item_title)}</span>'
            html += '<table style="margin: 10px 0; border-collapse: collapse; width: 100%;">'
            for col in columns:
                # Process column content - check for Sentence elements
                col_content = ""
                sentences_in_col = col.findall('Sentence')
                if sentences_in_col:
                    # Process Sentence elements properly
                    for sentence in sentences_in_col:
                        if processor:
                            col_content += processor.process_element(sentence, context)
                        else:
                            col_content += process_sentence(sentence, context)
                else:
                    # Fallback to simple text extraction or process children
                    if processor:
                        col_content = processor.process_children(col, context)
                        if not col_content.strip():
                            col_text = get_text(col)
                            if col_text:
                                col_content = escape_html(col_text)
                    else:
                        col_text = get_text(col)
                        if col_text:
                            col_content = escape_html(col_text)
                
                if col_content.strip():
                    html += f'<tr><td style="padding: 5px; border: 1px solid #ddd;">{col_content}</td></tr>'
            html += '</table></div>'
            return html
    
    processor = context.get('processor') if context else None
    
    sentences_html = ""
    for sentence in element.findall('ItemSentence/Sentence'):
        if processor:
            sentences_html += processor.process_element(sentence, context)
        else:
            sentences_html += process_sentence(sentence, context)
    
    subitem1s_html = ""
    for subitem1 in element.findall('Subitem1'):
        if processor:
            subitem1s_html += processor.process_element(subitem1, context)
        else:
            subitem1s_html += process_subitem1(subitem1, context)
    
    html = '<div class="item" style="margin: 10px 0; padding-left: 30px;">'
    if item_title:
        html += f'<span class="item-title" style="font-weight: bold; color: #27ae60; margin-right: 10px;">{escape_html(item_title)}</span>'
    html += sentences_html
    html += subitem1s_html
    html += '</div>'
    return html


def process_subitem1(element: ET.Element, context: Dict = None) -> str:
    """Process Subitem1 element"""
    subitem_title = get_text(element.find('Subitem1Title'))
    
    processor = context.get('processor') if context else None
    
    sentences_html = ""
    for sentence in element.findall('Subitem1Sentence/Sentence'):
        if processor:
            sentences_html += processor.process_element(sentence, context)
        else:
            sentences_html += process_sentence(sentence, context)
    
    subitem2s_html = ""
    for subitem2 in element.findall('Subitem2'):
        subitem2_title = get_text(subitem2.find('Subitem2Title'))
        subitem2_sentences = ""
        for sentence in subitem2.findall('Subitem2Sentence/Sentence'):
            if processor:
                subitem2_sentences += processor.process_element(sentence, context)
            else:
                subitem2_sentences += process_sentence(sentence, context)
        
        subitem2s_html += f'<div class="subitem2" style="margin: 5px 0; padding-left: 20px;">'
        if subitem2_title:
            subitem2s_html += f'<span class="item-title" style="color: #e67e22;">{escape_html(subitem2_title)}</span>'
        subitem2s_html += subitem2_sentences
        subitem2s_html += '</div>'
    
    html = '<div class="subitem1" style="margin: 8px 0; padding-left: 15px;">'
    if subitem_title:
        html += f'<span class="item-title" style="color: #d35400;">{escape_html(subitem_title)}</span>'
    html += sentences_html
    html += subitem2s_html
    html += '</div>'
    return html


def process_table_struct(element: ET.Element, context: Dict = None) -> str:
    """Process TableStruct element"""
    table_title = get_text(element.find('TableStructTitle'))
    table_elem = element.find('Table')
    
    if table_elem is None:
        return ""
    
    processor = context.get('processor') if context else None
    
    html = '<div class="table-wrapper" style="margin: 20px 0; overflow-x: auto;">'
    if table_title:
        html += f'<div class="article-caption" style="margin-bottom: 10px; font-weight: bold;">{escape_html(table_title)}</div>'
    html += '<table style="border-collapse: collapse; width: 100%; border: 1px solid #ddd;">'
    
    for row in table_elem.findall('TableRow'):
        html += '<tr>'
        for col in row.findall('TableColumn'):
            border_top = '1px solid #333' if col.get('BorderTop') == 'solid' else 'none'
            border_bottom = '1px solid #333' if col.get('BorderBottom') == 'solid' else 'none'
            border_left = '1px solid #333' if col.get('BorderLeft') == 'solid' else 'none'
            border_right = '1px solid #333' if col.get('BorderRight') == 'solid' else 'none'
            
            rowspan = col.get('rowspan', '')
            rowspan_attr = f' rowspan="{rowspan}"' if rowspan else ''
            colspan = col.get('colspan', '')
            colspan_attr = f' colspan="{colspan}"' if colspan else ''
            
            # Process column content - check for Sentence elements
            col_content = ""
            sentences_in_col = col.findall('Sentence')
            if sentences_in_col:
                # Process Sentence elements properly
                for sentence in sentences_in_col:
                    if processor:
                        col_content += processor.process_element(sentence, context)
                    else:
                        col_content += process_sentence(sentence, context)
            else:
                # Fallback to simple text extraction or process children
                if processor:
                    # Use processor to handle any children
                    col_content = processor.process_children(col, context)
                    if not col_content.strip():
                        col_text = get_text(col)
                        if col_text:
                            col_content = escape_html(col_text)
                else:
                    col_text = get_text(col)
                    if col_text:
                        col_content = escape_html(col_text)
            
            style = f"border-top: {border_top}; border-bottom: {border_bottom}; border-left: {border_left}; border-right: {border_right}; padding: 8px; vertical-align: top;"
            
            html += f'<td style="{style}"{rowspan_attr}{colspan_attr}>{col_content}</td>'
        html += '</tr>'
    
    html += '</table></div>'
    return html


def process_suppl_provision(element: ET.Element, context: Dict = None) -> str:
    """Process SupplProvision element"""
    suppl_label = get_text(element.find('SupplProvisionLabel'))
    amend_num = element.get('AmendLawNum', '') or element.get('AmendNum', '')
    
    processor = context.get('processor') if context else None
    
    articles_html = ""
    for article in element.findall('Article'):
        if processor:
            articles_html += processor.process_element(article, context)
        else:
            articles_html += process_article(article, context)
    
    paragraphs_html = ""
    for paragraph in element.findall('Paragraph'):
        paragraph_caption = get_text(paragraph.find('ParagraphCaption'))
        paragraph_content = ""
        if processor:
            paragraph_content = processor.process_element(paragraph, context)
        else:
            paragraph_content = process_paragraph(paragraph, context)
        
        paragraphs_html += '<div class="paragraph-section">'
        if paragraph_caption:
            paragraphs_html += f'<div class="article-caption">{escape_html(paragraph_caption)}</div>'
        paragraphs_html += paragraph_content
        paragraphs_html += '</div>'
    
    suppl_id = "suppl-provision"
    html = f'<div class="chapter" id="{suppl_id}" style="margin: 40px 0; border-top: 2px solid #e0e0e0; padding-top: 20px;">'
    if suppl_label:
        html += f'<div class="chapter-title" style="font-size: 1.5em; font-weight: bold; color: #2c3e50; margin-bottom: 20px;">{escape_html(suppl_label)}</div>'
    if amend_num:
        html += f'<div class="document-meta" style="margin-bottom: 15px;">{escape_html(amend_num)}</div>'
    html += articles_html
    html += paragraphs_html
    html += '</div>'
    return html


def process_appdx_table(element: ET.Element, context: Dict = None) -> str:
    """Process AppdxTable element"""
    appdx_title = get_text(element.find('AppdxTableTitle'))
    related_article = get_text(element.find('RelatedArticleNum'))
    
    processor = context.get('processor') if context else None
    
    table_html = ""
    table_struct = element.find('TableStruct')
    if table_struct is not None:
        if processor:
            table_html = processor.process_element(table_struct, context)
        else:
            table_html = process_table_struct(table_struct, context)
    else:
        table_elem = element.find('Table')
        if table_elem is not None:
            temp_table_struct = ET.Element('TableStruct')
            temp_table_struct.append(table_elem)
            if processor:
                table_html = processor.process_element(temp_table_struct, context)
            else:
                table_html = process_table_struct(temp_table_struct, context)
    
    html = '<div class="appdx-table" style="margin: 30px 0; padding: 20px; background: #f8f9fa; border-radius: 5px;">'
    if appdx_title:
        html += f'<div class="chapter-title" style="margin-bottom: 10px;">{escape_html(appdx_title)}</div>'
    if related_article:
        html += f'<div class="document-meta" style="margin-bottom: 15px; font-style: italic;">{escape_html(related_article)}</div>'
    html += table_html
    html += '</div>'
    return html


def get_all_processors() -> Dict[str, Callable]:
    """Get all default processors"""
    return {
        'Document': process_document,
        'DocumentTitle': process_document_title,
        'EnactStatement': process_enact_statement,
        'TOC': process_toc,
        'Chapter': process_chapter,
        'Section': process_section,
        'Subsection': process_subsection,
        'Article': process_article,
        'Paragraph': process_paragraph,
        'Sentence': process_sentence,
        'Item': process_item,
        'Subitem1': process_subitem1,
        'TableStruct': process_table_struct,
        'SupplProvision': process_suppl_provision,
        'AppdxTable': process_appdx_table,
    }

