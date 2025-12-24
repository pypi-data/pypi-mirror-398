#!/usr/bin/env python3
"""
Test script for the shorthand parser
"""

from jexpand.shorthand_parser import ShorthandParser

def test_parser():
    """Test the shorthand parser with various patterns"""
    
    parser = ShorthandParser()
    
    test_cases = [
        ('f("test.py")', '{{ include_file(\'test.py\') }}'),
        ('f_xml_lines("src/main.py")', '{{ include_file(\'src/main.py\', format_as=\'xml\', line_numbers=\'short\') }}'),
        ('file_xml("config.yaml")', '{{ include_file(\'config.yaml\', format_as=\'xml\') }}'),
        ('dir_xml_lines("src/")', '{{ include_folder(\'src/\', format_as=\'xml\', line_numbers=\'short\') }}'),
        ('d_xml_fulllines("docs/")', '{{ include_folder(\'docs/\', format_as=\'xml\', line_numbers=\'full\') }}'),
        ('f_s10_e30("large_file.py")', '{{ include_file(\'large_file.py\', start_line=10, end_line=30) }}'),
        ('f_s5("partial.py")', '{{ include_file(\'partial.py\', start_line=5) }}'),
        ('f_e20("beginning.py")', '{{ include_file(\'beginning.py\', end_line=20) }}'),
        ('f_lines("numbered.py")', '{{ include_file(\'numbered.py\', line_numbers=\'short\') }}'),
        ('f_fulllines("detailed.py")', '{{ include_file(\'detailed.py\', line_numbers=\'full\') }}'),
        ('d("project/")', '{{ include_folder(\'project/\') }}'),
        ('d_xml("source/")', '{{ include_folder(\'source/\', format_as=\'xml\') }}'),
        ('d_lines("scripts/")', '{{ include_folder(\'scripts/\', line_numbers=\'short\') }}'),
        ('d_fulllines("examples/")', '{{ include_folder(\'examples/\', line_numbers=\'full\') }}'),
        ('>>>>| src/file.py', '{{ include_file(\'src/file.py\') }}'),
        ('>>>>| -d src/', '{{ include_folder(\'src/\') }}'),
        ('>>>>| -f -s 10 -e 20 src/app.py', '{{ include_file(\'src/app.py\', start_line=10, end_line=20) }}'),
        ('>>>>| -x -l templates/page.html', '{{ include_file(\'templates/page.html\', format_as=\'xml\', line_numbers=\'short\') }}'),
        ('>>>>| --directory --full docs', '{{ include_folder(\'docs\', line_numbers=\'full\') }}'),
        ('>>>>| -f src/module.py:L5-L15', '{{ include_file(\'src/module.py\', start_line=5, end_line=15) }}'),
    ]
    
    print("Testing shorthand parser...")
    print("=" * 60)
    
    all_passed = True
    
    for input_text, expected in test_cases:
        result = parser.parse_line(input_text)
        if result == expected:
            print(f"✓ {input_text:<30} -> {result}")
        else:
            print(f"✗ {input_text:<30} -> {result}")
            print(f"  Expected: {expected}")
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
    
    return all_passed

if __name__ == "__main__":
    test_parser()
