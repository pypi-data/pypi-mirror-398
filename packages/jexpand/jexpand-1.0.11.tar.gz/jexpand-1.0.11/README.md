# JExpand - Jinja2 Template File Expander

Enhanced file expansion using Jinja2 templates with flexible functionality for including files, conditional content, and more.

## Installation

```bash
pip install jexpand
```

## Usage

### Command Line Interface

JExpand now uses a modern argparse-based CLI with explicit input/output handling:

```bash
# Print to stdout
jexpand template.md

# Write to file
jexpand template.md -o expanded.md
jexpand template.md --output expanded.md

# Copy to clipboard
jexpand template.md -c
jexpand template.md --clipboard

# Non-strict mode (don't fail on missing files)
jexpand template.md --no-strict

# Specify template directory
jexpand template.md --template-dir /path/to/templates

# Show help
jexpand --help

# CLI mode: Include entire directory contents
jexpand /path/to/directory --mode cli -o output.md
```

#### CLI Mode for Directory Processing

JExpand includes a special CLI mode that allows you to quickly include all files from a directory without writing a template:

```bash
# Include all files from a directory
jexpand /path/to/docs --mode cli -o documentation.md

# This is equivalent to creating a template with:
# {{ include_folder('/path/to/docs') }}
```

The CLI mode automatically:
- Creates a temporary template with `{{ include_folder('directory_path') }}`
- Processes all files in the specified directory
- Outputs them in XML format with file paths and contents
- Cleans up the temporary template file

This is particularly useful for:
- Quick documentation generation from source directories
- Exporting entire project structures
- Creating backups of directory contents in readable format

### Clipboard Support

JExpand can copy the expanded template directly to your system clipboard:

```bash
# Copy expanded template to clipboard
jexpand template.md --clipboard
jexpand template.md -c

# Also works with CLI mode
jexpand /path/to/docs --mode cli --clipboard
```

This is useful for:
- Quickly sharing expanded content
- Pasting into documents or editors
- Working with templates without creating intermediate files

### Python Module

```bash
# Run as module
python -m jexpand template.md -o expanded.md

# Copy to clipboard via module
python -m jexpand template.md --clipboard
```

### Python API

```python
from jexpand import JinjaFileExpander

# Create expander
expander = JinjaFileExpander(strict_mode=True)

# Expand to file
expander.expand_file(
    template_path="template.md",
    output_path="output.md"
)

# Expand to string
result = expander.expand_file("template.md")

# Copy to clipboard
expander.expand_file(
    template_path="template.md",
    copy_to_clipboard=True
)

# Simple expansion with {file} syntax
result = expander.simple_expand("simple_template.md")
```

### Template Features

JExpand supports powerful Jinja2 templates with custom functions and filters:

#### Custom Functions

- `include_file(path)` - Include the contents of a file
- `file_exists(path)` - Check if a file exists
- `file_size(path)` - Get file size in bytes
- `file_extension(path)` - Get file extension
- `basename(path)` - Get basename of file
- `dirname(path)` - Get directory name of file

#### Custom Filters

- `code_block(language)` - Wrap content in markdown code block
- `indent(spaces)` - Indent each line with specified spaces
- `comment_out(comment_char)` - Comment out each line
- `line_numbers(format='short')` - Add line numbers to content
  - `format='short'`: outputs as "1 | content"
  - `format='full'`: outputs as "line 1 | content"

#### Example Template

```jinja2
# My Project Documentation

## Source Implementation
{{ include_file('src/main.py') | code_block('python') }}

## Source with Line Numbers
{{ include_file('src/main.py') | line_numbers | code_block('python') }}

## Configuration
{% if file_exists('config.yaml') %}
{{ include_file('config.yaml') | code_block('yaml') }}
{% else %}
No configuration file found.
{% endif %}

## Multiple Files
{% for file_path in ['file1.py', 'file2.py'] %}
### {{ basename(file_path) }}
{{ include_file(file_path) | indent(4) }}
{% endfor %}

## File Information
{% for file in ['app.py', 'utils.py'] %}
{% if file_exists(file) %}
- **{{ file }}**: {{ file_size(file) }} bytes
{% endif %}
{% endfor %}
```

### Simple Syntax (Backward Compatibility)

JExpand also supports a simpler `{file_path}` syntax that gets converted to Jinja2:

```python
from jexpand import JinjaFileExpander

expander = JinjaFileExpander()
# Converts {/path/to/file} to {{ include_file('/path/to/file') }}
expander.simple_expand("simple_template.md")
```

## Advanced Usage

### Programmatic Generation

You can use jexpand programmatically to generate documentation:

```python
#!/usr/bin/env python3
from jexpand import JinjaFileExpander
from pathlib import Path

def generate_docs(source_dir, output_dir):
    """Generate documentation for all source files."""
    expander = JinjaFileExpander(strict_mode=True)
    
    for source_file in Path(source_dir).glob("*.py"):
        template_content = f"""
# {source_file.name} Documentation

## Source Code
{{{{ include_file('{source_file}') | code_block('python') }}}}

## Analysis
**File:** {source_file.name}
**Size:** {{{{ file_size('{source_file}') }}}} bytes
"""
        
        # Expand template
        result = expander.expand_string(template_content)
        
        # Write to output
        output_file = Path(output_dir) / f"{source_file.stem}_docs.md"
        with open(output_file, 'w') as f:
            f.write(result)

# Usage
generate_docs("src/", "docs/")
```

## Recent Improvements (v1.0.2)

### Enhanced CLI Interface
- **Modern argparse-based CLI** replacing the previous fire-based interface
- **Explicit input/output handling** with `-o`/`--output` flags
- **Better error messages** and help text
- **Proper exit codes** for scripting

### Bug Fixes
- **Fixed double printing issue** that caused duplicated output
- **Improved absolute path handling** for template files
- **Fixed Template constructor** compatibility issues
- **Removed subprocess overhead** in programmatic usage

### Performance Improvements
- **Direct import support** - no subprocess calls needed
- **Cleaner output handling** - no extra newlines or duplication
- **Reduced dependencies** - removed fire dependency

### Backward Compatibility
- **Simple expansion syntax** still supported via `simple_expand()`
- **Legacy `expand_file()` function** remains available
- **All existing templates** continue to work

## Development

### Local Installation

```bash
# Install in development mode
pip install -e .

# Test the command
jexpand --help
```

### Package Structure

```
jexpand/
├── jexpand/
│   ├── __init__.py      # Package exports and main entry point
│   ├── __main__.py      # Module entry point for python -m jexpand
│   └── main.py          # Core functionality and CLI
├── setup.py             # Package configuration
├── README.md            # This file
└── .gitignore          # Git ignore rules
```

## Examples

See the `examples/` directory (if present) or check the GitHub repository for real-world usage examples.

## License

MIT License 

## Links

- **PyPI**: https://pypi.org/project/jexpand/
- **GitHub**: https://github.com/OhadRubin/jexpand
- **Issues**: https://github.com/OhadRubin/jexpand/issues 