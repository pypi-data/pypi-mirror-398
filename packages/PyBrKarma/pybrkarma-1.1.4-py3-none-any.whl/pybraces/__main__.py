#!/usr/bin/env python3
"""
PyBr - Python with Braces Command Line Interface
Entry point for running PyBr from command line
"""

import sys
import argparse
from . import run_pybr, convert_pybr_to_py

def main():
    """Main entry point for PyBr command line interface"""
    parser = argparse.ArgumentParser(
        description='PyBr - Python with Braces',
        prog='pybraces'
    )
    parser.add_argument('file', help='PyBr file to run or convert')
    parser.add_argument('--convert', '-c', action='store_true', help='Convert to Python file')
    parser.add_argument('--debug', '-d', action='store_true', help='Enable debug mode')
    parser.add_argument('--output', '-o', help='Output file for conversion')
    parser.add_argument('--version', action='version', version='%(prog)s 1.0.0')

    args = parser.parse_args()

    try:
        if args.convert or args.output:
            # Convert mode
            output_path = args.output or args.file.replace('.pybr', '.py')
            result = convert_pybr_to_py(args.file, output_path)
            print(f"Converted {args.file} to {output_path}")
            if args.debug:
                print("Converted code:")
                print(result)
        else:
            # Run mode
            run_pybr(args.file)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except SyntaxError as e:
        print(f"Syntax Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()