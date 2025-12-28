"""Command-line interface for tgconvert"""

import argparse
import sys
import json
from pathlib import Path
from . import SessionConverter, __version__


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Universal Telegram session converter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert Telethon to Pyrogram
  tgconvert -i session.session -o output.session -if telethon -of pyrogram
  
  # Auto-detect input format
  tgconvert -i session.session -o output.session -of pyrogram
  
  # Convert to tdata
  tgconvert -i session.session -o ./tdata/ -of tdata
  
  # Convert to auth key string
  tgconvert -i session.session -o authkey.txt -of authkey
  
  # Get session info
  tgconvert -i session.session --info
  
  # List supported formats
  tgconvert --list-formats

Supported formats:
  - telethon   : Telethon .session files (SQLite)
  - pyrogram   : Pyrogram .session files (SQLite)
  - tdata      : Telegram Desktop tdata directory
  - authkey    : Auth key string format (hex:dc_id)
        """
    )
    
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"tgconvert {__version__}"
    )
    
    parser.add_argument(
        "-i", "--input",
        help="Input session path (file, directory, or auth key string)"
    )
    
    parser.add_argument(
        "-o", "--output",
        help="Output session path"
    )
    
    parser.add_argument(
        "-if", "--input-format",
        choices=SessionConverter.list_formats(),
        help="Input format (auto-detect if not specified)"
    )
    
    parser.add_argument(
        "-of", "--output-format",
        choices=SessionConverter.list_formats(),
        help="Output format"
    )
    
    parser.add_argument(
        "--info",
        action="store_true",
        help="Show session information without converting"
    )
    
    parser.add_argument(
        "--list-formats",
        action="store_true",
        help="List all supported formats"
    )
    
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format"
    )
    
    args = parser.parse_args()
    
    # Handle list-formats
    if args.list_formats:
        converter = SessionConverter()
        formats = converter.list_formats()
        
        if args.json:
            format_info = [converter.get_format_info(f) for f in formats]
            print(json.dumps(format_info, indent=2))
        else:
            print("Supported formats:")
            for fmt in formats:
                info = converter.get_format_info(fmt)
                print(f"  {fmt:12} - {info['display_name']}")
        
        return 0
    
    # Require input for other operations
    if not args.input:
        parser.error("the following arguments are required: -i/--input")
    
    converter = SessionConverter()
    
    try:
        # Handle info command
        if args.info:
            info = converter.get_info(args.input, args.input_format)
            
            if args.json:
                print(json.dumps(info, indent=2))
            else:
                print("Session Information:")
                print(f"  Format:       {info['format']}")
                print(f"  DC ID:        {info['dc_id']}")
                print(f"  User ID:      {info['user_id'] or 'Unknown'}")
                print(f"  Is Bot:       {info['is_bot']}")
                print(f"  API ID:       {info['api_id'] or 'Unknown'}")
                print(f"  Server:       {info['server'] or 'Unknown'}")
                print(f"  Port:         {info['port'] or 'Unknown'}")
                print(f"  Auth Key:     {info['auth_key_hash']}... (truncated)")
            
            return 0
        
        # Handle conversion
        if not args.output:
            parser.error("the following arguments are required: -o/--output")
        
        if not args.output_format:
            parser.error("the following arguments are required: -of/--output-format")
        
        # Detect input format if not specified
        if not args.input_format:
            detected = converter.detect_format(args.input)
            if detected:
                print(f"Detected input format: {detected}")
            else:
                print("Error: Could not detect input format. Please specify with -if/--input-format")
                return 1
        
        # Perform conversion
        print(f"Converting {args.input} -> {args.output}")
        print(f"Format: {args.input_format or 'auto'} -> {args.output_format}")
        
        session_data = converter.convert(
            input_path=args.input,
            output_path=args.output,
            input_format=args.input_format,
            output_format=args.output_format,
        )
        
        print("✓ Conversion successful!")
        
        if args.json:
            result = {
                "success": True,
                "input": args.input,
                "output": args.output,
                "input_format": args.input_format or converter.detect_format(args.input),
                "output_format": args.output_format,
                "dc_id": session_data.dc_id,
                "user_id": session_data.user_id,
            }
            print(json.dumps(result, indent=2))
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        
        if args.json:
            error_result = {
                "success": False,
                "error": str(e),
            }
            print(json.dumps(error_result, indent=2))
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
