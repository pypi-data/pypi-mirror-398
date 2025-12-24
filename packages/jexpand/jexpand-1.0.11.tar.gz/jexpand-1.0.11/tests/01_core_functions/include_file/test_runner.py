#!/usr/bin/env python3
"""
Test runner for include_file function
"""

import os
import sys
import subprocess

def run_test():
    """Run the include_file test"""
    print("=" * 60)
    print("Testing include_file function")
    print("=" * 60)
    
    # Change to workspace directory
    os.chdir('/workspace')
    
    # Test 1: Basic expansion (should work)
    print("\n1. Testing basic expansion:")
    try:
        result = subprocess.run([
            'python3', '-m', 'jexpand', 
            'tests/01_core_functions/include_file/template.md'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ SUCCESS: Basic expansion worked")
            print("Output preview:")
            print(result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout)
        else:
            print("❌ FAILED: Basic expansion failed")
            print(f"Error: {result.stderr}")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Test 2: Non-strict mode (should work with missing files)
    print("\n2. Testing non-strict mode:")
    try:
        result = subprocess.run([
            'python3', '-m', 'jexpand', 
            'tests/01_core_functions/include_file/template.md',
            '--no-strict'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ SUCCESS: Non-strict mode worked")
            # Check if it handles missing files gracefully
            if 'Default content when file is missing' in result.stdout:
                print("✅ Default value handling works correctly")
            else:
                print("⚠️  Default value handling may not be working as expected")
        else:
            print("❌ FAILED: Non-strict mode failed")
            print(f"Error: {result.stderr}")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Test 3: Output to file
    print("\n3. Testing output to file:")
    try:
        output_file = 'tests/01_core_functions/include_file/output.md'
        result = subprocess.run([
            'python3', '-m', 'jexpand', 
            'tests/01_core_functions/include_file/template.md',
            '-o', output_file
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and os.path.exists(output_file):
            print("✅ SUCCESS: Output to file worked")
            with open(output_file, 'r') as f:
                content = f.read()
                print(f"Generated file size: {len(content)} characters")
        else:
            print("❌ FAILED: Output to file failed")
            print(f"Error: {result.stderr}")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    print("\n" + "=" * 60)
    print("include_file function test completed")
    print("=" * 60)

if __name__ == "__main__":
    run_test()