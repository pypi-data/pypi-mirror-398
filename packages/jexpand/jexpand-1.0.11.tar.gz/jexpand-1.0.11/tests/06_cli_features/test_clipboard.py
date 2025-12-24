#!/usr/bin/env python3
"""
Test script for clipboard functionality
"""

import tempfile
import os
from jexpand.main import JinjaFileExpander

def test_clipboard_functionality():
    """Test basic clipboard functionality"""
    
    # Create a simple test template
    template_content = """Test clipboard content:
{{ include_file('test_data.txt', default='Test file content') }}

This should be copied to clipboard.
"""
    
    # Create temporary template file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as temp_file:
        temp_file.write(template_content)
        template_path = temp_file.name
    
    try:
        # Create expander in non-strict mode to handle missing test_data.txt
        expander = JinjaFileExpander(strict_mode=False)
        
        # Test direct copy to clipboard
        print("Testing clipboard functionality...")
        result = expander.expand_file(template_path, copy_to_clipboard=True)
        
        print(f"Template expanded and copied to clipboard. Result length: {len(result)} characters")
        print("Content that should be in clipboard:")
        print("-" * 40)
        print(result)
        print("-" * 40)
        
        # Test the copy_to_clipboard method directly
        test_text = "Direct test of clipboard functionality"
        if expander.copy_to_clipboard(test_text):
            print(f"✓ Direct clipboard test successful")
        else:
            print("✗ Direct clipboard test failed")
            
    finally:
        # Clean up temporary file
        os.unlink(template_path)

if __name__ == "__main__":
    test_clipboard_functionality()