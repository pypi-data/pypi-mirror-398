#!/usr/bin/env python3
"""
Shorthand parser for jexpand - converts shorthand syntax to Jinja2 template calls

Supported shorthand syntax:
- f("path") -> {{ include_file('path') }}
- f_xml_lines("path") -> {{ include_file('path', format_as='xml', line_numbers='short') }}
- file_xml("path") -> {{ include_file('path', format_as='xml') }}
- dir_xml_lines("path") -> {{ include_folder('path', format_as='xml', line_numbers='short') }}
- d_xml_fulllines("path") -> {{ include_folder('path', format_as='xml', line_numbers='full') }}
- f_s10_e30("path") -> {{ include_file('path', start_line=10, end_line=30) }}
- f_s10("path") -> {{ include_file('path', start_line=10) }}
- f_e30("path") -> {{ include_file('path', end_line=30) }}
- f_lines("path") -> {{ include_file('path', line_numbers='short') }}
- f_fulllines("path") -> {{ include_file('path', line_numbers='full') }}
"""

import re
import shlex
from typing import Dict, Callable, Optional


class ShorthandParser:
    """Parser for converting shorthand syntax to Jinja2 template calls"""
    
    def __init__(self):
        """Initialize the parser with pattern definitions"""
        self.patterns = self._build_patterns()
    
    def _build_patterns(self) -> Dict[str, Callable[[re.Match], str]]:
        """Build regex patterns and their corresponding conversion functions"""
        
        patterns = {}
        
        # f("path") -> {{ include_file('path') }}
        patterns[r'f\("([^"]+)"\)'] = lambda m: f"{{{{ include_file('{m.group(1)}') }}}}"
        
        # f_xml_lines("path") -> {{ include_file('path', format_as='xml', line_numbers='short') }}
        patterns[r'f_xml_lines\("([^"]+)"\)'] = lambda m: f"{{{{ include_file('{m.group(1)}', format_as='xml', line_numbers='short') }}}}"
        
        # file_xml("path") -> {{ include_file('path', format_as='xml') }}
        patterns[r'file_xml\("([^"]+)"\)'] = lambda m: f"{{{{ include_file('{m.group(1)}', format_as='xml') }}}}"
        
        
        # dir_xml_lines("path") -> {{ include_folder('path', format_as='xml', line_numbers='short') }}
        patterns[r'dir_xml\("([^"]+)"\)'] = lambda m: f"{{{{ include_folder('{m.group(1)}', format_as='xml') }}}}"
        patterns[r'dir_xml_lines\("([^"]+)"\)'] = lambda m: f"{{{{ include_folder('{m.group(1)}', format_as='xml', line_numbers='short') }}}}"
        
        # d_xml_fulllines("path") -> {{ include_folder('path', format_as='xml', line_numbers='full') }}
        patterns[r'd_xml_fulllines\("([^"]+)"\)'] = lambda m: f"{{{{ include_folder('{m.group(1)}', format_as='xml', line_numbers='full') }}}}"
        
        # f_s<start>_e<end>("path") -> {{ include_file('path', start_line=<start>, end_line=<end>) }}
        patterns[r'f_s(\d+)_e(\d+)\("([^"]+)"\)'] = lambda m: f"{{{{ include_file('{m.group(3)}', start_line={m.group(1)}, end_line={m.group(2)}) }}}}"
        
        # f_s<start>("path") -> {{ include_file('path', start_line=<start>) }}
        patterns[r'f_s(\d+)\("([^"]+)"\)'] = lambda m: f"{{{{ include_file('{m.group(2)}', start_line={m.group(1)}) }}}}"
        
        # f_e<end>("path") -> {{ include_file('path', end_line=<end>) }}
        patterns[r'f_e(\d+)\("([^"]+)"\)'] = lambda m: f"{{{{ include_file('{m.group(2)}', end_line={m.group(1)}) }}}}"
        
        # f_lines("path") -> {{ include_file('path', line_numbers='short') }}
        patterns[r'f_lines\("([^"]+)"\)'] = lambda m: f"{{{{ include_file('{m.group(1)}', line_numbers='short') }}}}"
        
        # f_fulllines("path") -> {{ include_file('path', line_numbers='full') }}
        patterns[r'f_fulllines\("([^"]+)"\)'] = lambda m: f"{{{{ include_file('{m.group(1)}', line_numbers='full') }}}}"
        
        # d("path") -> {{ include_folder('path') }}
        patterns[r'd\("([^"]+)"\)'] = lambda m: f"{{{{ include_folder('{m.group(1)}') }}}}"
        
        # d_xml("path") -> {{ include_folder('path', format_as='xml') }}
        patterns[r'd_xml\("([^"]+)"\)'] = lambda m: f"{{{{ include_folder('{m.group(1)}', format_as='xml') }}}}"
        
        # d_lines("path") -> {{ include_folder('path', line_numbers='short') }}
        patterns[r'd_lines\("([^"]+)"\)'] = lambda m: f"{{{{ include_folder('{m.group(1)}', line_numbers='short') }}}}"
        
        # d_fulllines("path") -> {{ include_folder('path', line_numbers='full') }}
        patterns[r'd_fulllines\("([^"]+)"\)'] = lambda m: f"{{{{ include_folder('{m.group(1)}', line_numbers='full') }}}}"
        
        return patterns
    
    def parse_line(self, line: str) -> str:
        """Parse a single line and convert shorthand syntax to Jinja2"""
        converted_cli = self._convert_cli_shorthand(line)
        if converted_cli is not None:
            return converted_cli

        result = line

        # Apply patterns in order (more specific patterns first)
        for pattern, replacement_func in self.patterns.items():
            result = re.sub(pattern, replacement_func, result)

        return result
    
    def parse_content(self, content: str) -> str:
        """Parse entire content and convert all shorthand syntax"""
        lines = content.split('\n')
        parsed_lines = []

        for line in lines:
            parsed_line = self.parse_line(line)
            parsed_lines.append(parsed_line)

        return '\n'.join(parsed_lines)

    def _convert_cli_shorthand(self, line: str) -> Optional[str]:
        stripped = line.lstrip()
        indent = line[: len(line) - len(stripped)]

        if not stripped.startswith('>>>>|'):
            return None

        remainder = stripped[5:].strip()
        if not remainder:
            return line

        try:
            tokens = shlex.split(remainder)
        except ValueError:
            return line

        include_func = 'include_file'
        kwargs: Dict[str, object] = {}
        path_tokens = []
        i = 0

        while i < len(tokens):
            token = tokens[i]

            if token in ('-d', '--directory'):
                include_func = 'include_folder'
                i += 1
                continue

            if token in ('-f', '--file'):
                include_func = 'include_file'
                i += 1
                continue

            if token == '-x':
                kwargs['format_as'] = 'xml'
                i += 1
                continue

            if token == '-l':
                kwargs['line_numbers'] = 'short'
                i += 1
                continue

            if token == '--full':
                kwargs['line_numbers'] = 'full'
                i += 1
                continue

            if token == '-s':
                i += 1
                if i >= len(tokens):
                    return line
                try:
                    kwargs['start_line'] = int(tokens[i])
                except ValueError:
                    return line
                i += 1
                continue

            if token == '-e':
                i += 1
                if i >= len(tokens):
                    return line
                try:
                    kwargs['end_line'] = int(tokens[i])
                except ValueError:
                    return line
                i += 1
                continue

            path_tokens.extend(tokens[i:])
            break

        if not path_tokens:
            return line

        raw_path = ' '.join(path_tokens)
        path, path_start, path_end = self._extract_line_spec(raw_path)

        if path_start is not None and 'start_line' not in kwargs:
            kwargs['start_line'] = path_start
        if path_end is not None and 'end_line' not in kwargs:
            kwargs['end_line'] = path_end

        path = path.strip()
        if not path:
            return line

        escaped_path = path.replace('\\', '\\\\').replace("'", "\\'")
        args = [f"'{escaped_path}'"]

        for key in ('format_as', 'start_line', 'end_line', 'line_numbers'):
            if key not in kwargs:
                continue
            value = kwargs[key]
            if isinstance(value, str):
                args.append(f"{key}='{value}'")
            else:
                args.append(f"{key}={value}")

        args_str = ', '.join(args)
        converted = f"{{{{ {include_func}({args_str}) }}}}"
        return indent + converted

    def _extract_line_spec(self, path: str):
        match = re.search(r':L?(\d+)(?:-L?(\d+))?$', path)
        if not match:
            return path, None, None

        base_path = path[: match.start()]
        start_val = int(match.group(1)) if match.group(1) else None
        end_val = int(match.group(2)) if match.group(2) else None
        return base_path, start_val, end_val
    
    def parse_file(self, input_path: str, output_path: Optional[str] = None) -> str:
        """Parse a file and optionally write the result to another file"""
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        parsed_content = self.parse_content(content)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(parsed_content)
        
        return parsed_content
    
    def get_supported_patterns(self) -> Dict[str, str]:
        """Get a dictionary of supported patterns and their descriptions"""
        return {
            'f("path")': 'Include file content',
            'f_xml_lines("path")': 'Include file in XML format with short line numbers',
            'file_xml("path")': 'Include file in XML format',
            'dir_xml_lines("path")': 'Include directory in XML format with short line numbers',
            'd_xml_fulllines("path")': 'Include directory in XML format with full line numbers',
            'f_s10_e30("path")': 'Include file from line 10 to line 30',
            'f_s10("path")': 'Include file starting from line 10',
            'f_e30("path")': 'Include file up to line 30',
            'f_lines("path")': 'Include file with short line numbers',
            'f_fulllines("path")': 'Include file with full line numbers',
            'd("path")': 'Include directory content',
            'd_xml("path")': 'Include directory in XML format',
            'd_lines("path")': 'Include directory with short line numbers',
            'd_fulllines("path")': 'Include directory with full line numbers',
        }


def main():
    """Command line interface for the shorthand parser"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Convert shorthand syntax to Jinja2 template calls",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Supported shorthand patterns:

FILE OPERATIONS:
  f("path")                -> {{ include_file('path') }}
  f_lines("path")          -> {{ include_file('path', line_numbers='short') }}
  f_fulllines("path")      -> {{ include_file('path', line_numbers='full') }}
  f_s10("path")            -> {{ include_file('path', start_line=10) }}
  f_e30("path")            -> {{ include_file('path', end_line=30) }}
  f_s10_e30("path")        -> {{ include_file('path', start_line=10, end_line=30) }}

XML FILE OPERATIONS:
  file_xml("path")         -> {{ include_file('path', format_as='xml') }}
  f_xml_lines("path")      -> {{ include_file('path', format_as='xml', line_numbers='short') }}

DIRECTORY OPERATIONS:
  d("path")                -> {{ include_folder('path') }}
  d_lines("path")          -> {{ include_folder('path', line_numbers='short') }}
  d_fulllines("path")      -> {{ include_folder('path', line_numbers='full') }}

XML DIRECTORY OPERATIONS:
  d_xml("path")            -> {{ include_folder('path', format_as='xml') }}
  dir_xml_lines("path")    -> {{ include_folder('path', format_as='xml', line_numbers='short') }}
  d_xml_fulllines("path")  -> {{ include_folder('path', format_as='xml', line_numbers='full') }}

Examples:
  python shorthand_parser.py input.txt -o output.txt
  python shorthand_parser.py input.txt --list-patterns
        """
    )
    
    parser.add_argument('input_file', help='Input file to parse')
    parser.add_argument('-o', '--output', help='Output file (default: print to stdout)')
    parser.add_argument('--list-patterns', action='store_true', help='List all supported patterns')
    
    args = parser.parse_args()
    
    shorthand_parser = ShorthandParser()
    
    if args.list_patterns:
        print("Supported shorthand patterns:")
        print("=" * 50)
        for pattern, description in shorthand_parser.get_supported_patterns().items():
            print(f"{pattern:<25} -> {description}")
        return
    
    try:
        result = shorthand_parser.parse_file(args.input_file, args.output)
        
        if not args.output:
            print(result, end='')
        else:
            print(f"Parsed content written to: {args.output}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
