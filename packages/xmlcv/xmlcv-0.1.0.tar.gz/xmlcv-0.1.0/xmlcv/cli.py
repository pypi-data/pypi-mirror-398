"""
Command-line interface for XMLCV
"""

import argparse
from pathlib import Path
from .converter import XMLToHTMLConverter
from .converter_v2 import XMLConverter
from .config import ConverterConfig


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Convert XML files to various document formats',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert single file
  xmlcv input.xml -o output.html
  
  # Convert directory
  xmlcv input_dir/ -o output_dir/
  
  # Convert with PDF
  xmlcv input.xml --pdf
  
  # Analyze XML structure
  xmlcv input.xml --analyze
        """
    )
    
    parser.add_argument(
        'input',
        type=str,
        nargs='?',
        help='Input XML file or directory (not required with --list-plugins)'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        default=None,
        help='Output HTML file or directory (default: input_dir/html or input_file.html)'
    )
    parser.add_argument(
        '--pdf',
        action='store_true',
        help='Also convert HTML to PDF (requires weasyprint or pdfkit)'
    )
    parser.add_argument(
        '--no-index',
        action='store_true',
        help='Do not create index page'
    )
    parser.add_argument(
        '--analyze',
        action='store_true',
        help='Analyze XML structure and print information'
    )
    parser.add_argument(
        '--css',
        type=str,
        default=None,
        help='Path to custom CSS file'
    )
    parser.add_argument(
        '--config',
        type=str,
        default=None,
        help='Path to JSON configuration file'
    )
    parser.add_argument(
        '--format',
        type=str,
        default='html',
        help='Output format (default: html). Use --list-plugins to see available formats'
    )
    parser.add_argument(
        '--list-plugins',
        action='store_true',
        help='List all available output format plugins'
    )
    
    args = parser.parse_args()
    
    # Handle list-plugins (must be first, before checking input)
    if args.list_plugins:
        converter = XMLConverter()
        plugins = converter.list_plugins()
        
        print("📦 Available Output Format Plugins:")
        print("=" * 80)
        for plugin_info in plugins:
            status = "✅" if plugin_info.enabled else "❌"
            print(f"\n{status} {plugin_info.name.upper()}")
            print(f"   Description: {plugin_info.description}")
            print(f"   Version: {plugin_info.version}")
            if plugin_info.file_extensions:
                print(f"   Extensions: {', '.join(plugin_info.file_extensions)}")
            if plugin_info.dependencies:
                print(f"   Dependencies: {', '.join(plugin_info.dependencies)}")
                print(f"   Install: pip install 'xmlcv[{plugin_info.name}]'")
            else:
                print(f"   Dependencies: None (always available)")
        
        print("\n" + "=" * 80)
        print("💡 Install all formats: pip install 'xmlcv[all]'")
        return 0
    
    # Check if input is required
    if not args.input and not args.list_plugins:
        parser.error("the following arguments are required: input (or use --list-plugins)")
    
    if not args.input:
        return 0  # Already handled list-plugins
    
    input_path = Path(args.input)
    
    if not input_path.exists():
        print(f"❌ Error: {input_path} does not exist")
        return 1
    
    # Create config
    config = ConverterConfig()
    config.convert_to_pdf = args.pdf
    config.create_index = not args.no_index
    
    if args.css:
        config.css_file = Path(args.css)
    
    if args.config:
        import json
        with open(args.config, 'r') as f:
            config_dict = json.load(f)
            for key, value in config_dict.items():
                if hasattr(config, key):
                    setattr(config, key, value)
    
    # Create converter (use new XMLConverter for plugin system)
    if args.format != 'html' or args.list_plugins:
        converter_v2 = XMLConverter(config)
    else:
        # Use old converter for HTML (backward compatibility)
        converter = XMLToHTMLConverter(config)
        converter_v2 = None
    
    # Analyze mode
    if args.analyze:
        if input_path.is_file() and input_path.suffix == '.xml':
            if converter_v2:
                # Use new converter for analysis
                from .converter import XMLToHTMLConverter
                temp_converter = XMLToHTMLConverter(config)
                structure = temp_converter.analyze_xml(input_path)
            else:
                structure = converter.analyze_xml(input_path)
            
            print("📊 XML Structure Analysis:")
            print(f"  Elements found: {len(structure.get('elements', []))}")
            print(f"  Container elements: {len(structure.get('container_elements', []))}")
            print(f"  Text elements: {len(structure.get('text_elements', []))}")
            print("\n  Element hierarchy:")
            for parent, children in list(structure.get('hierarchy', {}).items())[:10]:
                print(f"    {parent} -> {', '.join(list(children)[:5])}")
        else:
            print("❌ Error: --analyze requires a single XML file")
            return 1
        return 0
    
    # Convert mode
    if input_path.is_file() and input_path.suffix == '.xml':
        # Convert single file
        if args.output:
            output_path = Path(args.output)
        else:
            output_path = input_path.with_suffix(f'.{args.format}')
        
        try:
            if converter_v2:
                # Use new plugin system
                success = converter_v2.convert(
                    input_path,
                    output_path,
                    output_format=args.format
                )
                if success:
                    print(f"✅ Converted: {input_path.name} -> {output_path.name} ({args.format})")
                else:
                    return 1
            else:
                # Use old HTML converter
                converter.convert_file(input_path, output_path)
                print(f"✅ Converted: {input_path.name} -> {output_path.name}")
        except Exception as e:
            print(f"❌ Error converting {input_path.name}: {e}")
            return 1
    
    elif input_path.is_dir():
        # Convert directory
        output_dir = Path(args.output) if args.output else None
        try:
            if converter_v2:
                # Use new plugin system for directory conversion
                xml_files = list(input_path.rglob("*.xml"))
                print(f"Found {len(xml_files)} XML files")
                
                for xml_file in xml_files:
                    rel_path = xml_file.relative_to(input_path)
                    if output_dir:
                        html_path = output_dir / rel_path.with_suffix(f'.{args.format}')
                    else:
                        html_path = xml_file.with_suffix(f'.{args.format}')
                    
                    html_path.parent.mkdir(parents=True, exist_ok=True)
                    success = converter_v2.convert(xml_file, html_path, output_format=args.format)
                    if success:
                        print(f"✅ Converted: {xml_file.name} -> {html_path.name}")
            else:
                # Use old converter
                converter.convert_directory(input_path, output_dir)
        except Exception as e:
            print(f"❌ Error converting directory: {e}")
            return 1
    
    else:
        print(f"❌ Error: {input_path} is not a valid XML file or directory")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

