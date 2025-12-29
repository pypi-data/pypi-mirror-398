# XMLCV

A flexible Python library for converting XML files to various document formats with dynamic element processing and plugin system.

## Features

- 🔄 **Dynamic Element Processing**: Automatically analyzes XML structure and processes elements accordingly
- 📄 **Multiple Format Support**: Handles various XML schemas by loading element definitions from XML
- 🎨 **Customizable Styling**: Support for custom CSS and styling options
- 📑 **Table of Contents**: Automatic TOC generation
- 📊 **PDF Export**: Optional PDF conversion using WeasyPrint or pdfkit
- 🔧 **Extensible**: Easy to add custom element processors

## Installation

### Basic Installation
```bash
pip install xmlcv
```

### Optional Dependencies

The package has optional dependencies for different output formats. You can install them individually or all at once:

```bash
# Install specific formats
pip install 'xmlcv[pdf]'      # PDF support
pip install 'xmlcv[docx]'      # DOCX support
pip install 'xmlcv[pptx]'    # PPTX support
pip install 'xmlcv[markdown]' # Markdown support

# Install multiple formats
pip install 'xmlcv[pdf,docx]'

# Install all formats
pip install 'xmlcv[all]'
```

### List Available Plugins

```bash
xmlcv --list-plugins
```

## Quick Start

### Command Line

```bash
# List available output formats
xmlcv --list-plugins

# Convert single file to HTML (default)
xmlcv input.xml -o output.html

# Convert to different formats
xmlcv input.xml --format pdf -o output.pdf
xmlcv input.xml --format docx -o output.docx

# Convert directory
xmlcv input_dir/ -o output_dir/

# Analyze XML structure
xmlcv input.xml --analyze
```

### Python API

#### Using XMLConverter (New Plugin System)

```python
from xmlcv import XMLConverter, ConverterConfig
from pathlib import Path

# Basic usage with plugin system
converter = XMLConverter()

# List available plugins
plugins = converter.list_plugins()
for plugin in plugins:
    print(f"{plugin.name}: {plugin.description}")

# Convert to different formats
converter.convert(Path("input.xml"), Path("output.html"), output_format="html")
converter.convert(Path("input.xml"), Path("output.pdf"), output_format="pdf")

# Convert to multiple formats at once
converter.convert_to_multiple_formats(
    Path("input.xml"),
    output_formats=["html", "pdf"]
)
```

#### Using XMLToHTMLConverter (Legacy API)

```python
from xmlcv import XMLToHTMLConverter, ConverterConfig
from pathlib import Path

# Basic usage
converter = XMLToHTMLConverter()
html = converter.convert_file(
    Path("input.xml"),
    Path("output.html")
)

# With custom configuration
config = ConverterConfig(
    convert_to_pdf=True,
    include_navigation=True,
    custom_css="/* your custom CSS */"
)
converter = XMLToHTMLConverter(config)
html = converter.convert_file(Path("input.xml"), Path("output.html"))

# Convert entire directory
converter.convert_directory(
    Path("xml_files/"),
    Path("html_output/")
)
```

## Advanced Usage

### Custom Element Processors

```python
from xmlcv import XMLToHTMLConverter, ConverterConfig
import xml.etree.ElementTree as ET

def custom_processor(element: ET.Element, context: dict) -> str:
    """Custom processor for a specific element"""
    text = element.text or ""
    return f'<div class="custom">{text}</div>'

# Register custom processor
config = ConverterConfig()
config.element_processors['CustomElement'] = custom_processor

converter = XMLToHTMLConverter(config)
```

### Analyzing XML Structure

```python
from xmlcv import XMLToHTMLConverter
from pathlib import Path

converter = XMLToHTMLConverter()
structure = converter.analyze_xml(Path("input.xml"))

print(f"Elements found: {structure['elements']}")
print(f"Hierarchy: {structure['hierarchy']}")
```

## Supported Elements

The converter dynamically supports various XML elements including:

- **Structure**: Document, Title, Body, MainContent
- **Organization**: Chapter, Section, Subsection, Article
- **Content**: Paragraph, Sentence, Item, Subitem1, Subitem2
- **Tables**: TableStruct, Table, TableRow, TableColumn
- **Special**: Statement, Provision, Appendix, TOC
- **Formatting**: Ruby (annotations), Sub (subscript), and more

## Configuration

### ConverterConfig Options

- `output_dir`: Output directory path
- `create_index`: Create index.html page
- `convert_to_pdf`: Enable PDF conversion
- `css_file`: Path to custom CSS file
- `custom_css`: Custom CSS string
- `include_toc`: Include table of contents
- `include_navigation`: Include navigation sidebar
- `element_processors`: Dictionary of custom element processors
- `pdf_options`: PDF generation options

## Requirements

- Python 3.8+
- lxml >= 4.9.0

Optional:
- weasyprint >= 59.0 (for PDF export)
- pdfkit >= 1.0.0 (alternative PDF export)

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Changelog

### 0.1.0
- Initial release
- Dynamic element processing
- Support for various XML structures
- PDF export support
- CLI interface

