#!/usr/bin/env python3
"""
Comprehensive test runner for all jexpand features
"""

import os
import sys
import subprocess
import time
from pathlib import Path

class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        self.workspace = Path('/workspace')
        
    def run_command(self, cmd, timeout=30, expect_failure=False):
        """Run a command and capture output"""
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=timeout,
                cwd=self.workspace
            )
            
            success = (result.returncode == 0) if not expect_failure else (result.returncode != 0)
            return success, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)
    
    def test_basic_functionality(self):
        """Test basic jexpand functionality"""
        print("\n" + "="*60)
        print("TESTING: Basic Functionality")
        print("="*60)
        
        # Test 1: Version check
        success, stdout, stderr = self.run_command(['python3', '-m', 'jexpand', '--version'])
        if success and '1.0.4' in stdout:
            print("✅ Version check passed")
            self.passed += 1
        else:
            print("❌ Version check failed")
            self.failed += 1
            self.errors.append(f"Version check: {stderr}")
        
        # Test 2: Help command
        success, stdout, stderr = self.run_command(['python3', '-m', 'jexpand', '--help'])
        if success and 'Enhanced file expansion' in stdout:
            print("✅ Help command passed")
            self.passed += 1
        else:
            print("❌ Help command failed")
            self.failed += 1
            self.errors.append(f"Help command: {stderr}")
    
    def test_core_functions(self):
        """Test core template functions"""
        print("\n" + "="*60)
        print("TESTING: Core Template Functions")
        print("="*60)
        
        tests = [
            ('include_file', 'tests/01_core_functions/include_file/template.md'),
            ('include_folder', 'tests/01_core_functions/include_folder/template.md'),
        ]
        
        for test_name, template_path in tests:
            if os.path.exists(template_path):
                success, stdout, stderr = self.run_command([
                    'python3', '-m', 'jexpand', template_path, '--no-strict'
                ])
                if success:
                    print(f"✅ {test_name} test passed")
                    self.passed += 1
                else:
                    print(f"❌ {test_name} test failed")
                    self.failed += 1
                    self.errors.append(f"{test_name}: {stderr}")
            else:
                print(f"⚠️  {test_name} template not found: {template_path}")
    
    def test_template_filters(self):
        """Test template filters"""
        print("\n" + "="*60)
        print("TESTING: Template Filters")
        print("="*60)
        
        filters = ['code_block', 'indent', 'comment_out', 'line_numbers']
        
        for filter_name in filters:
            template_path = f'tests/02_template_filters/{filter_name}/template.md'
            if os.path.exists(template_path):
                success, stdout, stderr = self.run_command([
                    'python3', '-m', 'jexpand', template_path
                ])
                if success:
                    print(f"✅ {filter_name} filter test passed")
                    self.passed += 1
                else:
                    print(f"❌ {filter_name} filter test failed")
                    self.failed += 1
                    self.errors.append(f"{filter_name} filter: {stderr}")
            else:
                print(f"⚠️  {filter_name} template not found")
    
    def test_compilation_features(self):
        """Test compilation features"""
        print("\n" + "="*60)
        print("TESTING: Compilation Features")
        print("="*60)
        
        # Test intermediate compilation
        template_path = 'tests/03_compilation_features/intermediate_compilation/template.md'
        if os.path.exists(template_path):
            # Test 1: Basic expansion
            success, stdout, stderr = self.run_command([
                'python3', '-m', 'jexpand', template_path
            ])
            if success:
                print("✅ Standard expansion passed")
                self.passed += 1
            else:
                print("❌ Standard expansion failed")
                self.failed += 1
                self.errors.append(f"Standard expansion: {stderr}")
            
            # Test 2: Intermediate compilation
            intermediate_file = 'tests/03_compilation_features/intermediate_compilation/intermediate.md'
            success, stdout, stderr = self.run_command([
                'python3', '-m', 'jexpand', template_path, 
                '--intermediate', intermediate_file
            ])
            if success and os.path.exists(intermediate_file):
                print("✅ Intermediate compilation passed")
                self.passed += 1
                
                # Test 3: Two-stage compilation
                final_file = 'tests/03_compilation_features/intermediate_compilation/final.md'
                success, stdout, stderr = self.run_command([
                    'python3', '-m', 'jexpand', template_path,
                    '--intermediate', intermediate_file,
                    '--final', final_file
                ])
                if success and os.path.exists(final_file):
                    print("✅ Two-stage compilation passed")
                    self.passed += 1
                else:
                    print("❌ Two-stage compilation failed")
                    self.failed += 1
                    self.errors.append(f"Two-stage compilation: {stderr}")
            else:
                print("❌ Intermediate compilation failed")
                self.failed += 1
                self.errors.append(f"Intermediate compilation: {stderr}")
        else:
            print("⚠️  Intermediate compilation template not found")
    
    def test_operating_modes(self):
        """Test strict and non-strict modes"""
        print("\n" + "="*60)
        print("TESTING: Operating Modes")
        print("="*60)
        
        # Test strict mode (should fail with missing files)
        strict_template = 'tests/04_operating_modes/strict_mode/template.md'
        if os.path.exists(strict_template):
            success, stdout, stderr = self.run_command([
                'python3', '-m', 'jexpand', strict_template
            ], expect_failure=True)
            if success:  # We expect this to fail
                print("✅ Strict mode correctly failed with missing files")
                self.passed += 1
            else:
                print("❌ Strict mode did not fail as expected")
                self.failed += 1
                self.errors.append("Strict mode should fail with missing files")
        
        # Test non-strict mode (should succeed with placeholders)
        nonstrict_template = 'tests/04_operating_modes/non_strict_mode/template.md'
        if os.path.exists(nonstrict_template):
            success, stdout, stderr = self.run_command([
                'python3', '-m', 'jexpand', nonstrict_template, '--no-strict'
            ])
            if success:
                print("✅ Non-strict mode passed")
                self.passed += 1
                if 'FILE NOT FOUND' in stdout or '<!--' in stdout:
                    print("✅ Non-strict mode shows appropriate placeholders")
                    self.passed += 1
                else:
                    print("⚠️  Non-strict mode may not be showing placeholders correctly")
            else:
                print("❌ Non-strict mode failed")
                self.failed += 1
                self.errors.append(f"Non-strict mode: {stderr}")
    
    def test_output_formats(self):
        """Test different output formats"""
        print("\n" + "="*60)
        print("TESTING: Output Formats")
        print("="*60)
        
        template_path = 'tests/05_output_formats/xml_format/template.md'
        if os.path.exists(template_path):
            success, stdout, stderr = self.run_command([
                'python3', '-m', 'jexpand', template_path
            ])
            if success:
                print("✅ Output formats test passed")
                self.passed += 1
                
                # Check if different formats are present in output
                if '<file path=' in stdout:
                    print("✅ XML format detected")
                    self.passed += 1
                if '<!-- File:' in stdout:
                    print("✅ Blocks format detected")
                    self.passed += 1
                if '=== FILE SEPARATOR ===' in stdout:
                    print("✅ Custom separator detected")
                    self.passed += 1
            else:
                print("❌ Output formats test failed")
                self.failed += 1
                self.errors.append(f"Output formats: {stderr}")
    
    def test_cli_features(self):
        """Test CLI-specific features"""
        print("\n" + "="*60)
        print("TESTING: CLI Features")
        print("="*60)
        
        template_path = 'tests/06_cli_features/basic_cli/template.md'
        if os.path.exists(template_path):
            # Test output to file
            output_file = 'tests/06_cli_features/basic_cli/output.md'
            success, stdout, stderr = self.run_command([
                'python3', '-m', 'jexpand', template_path, '-o', output_file
            ])
            if success and os.path.exists(output_file):
                print("✅ Output to file passed")
                self.passed += 1
                
                with open(output_file, 'r') as f:
                    content = f.read()
                    if len(content) > 0:
                        print("✅ Output file has content")
                        self.passed += 1
            else:
                print("❌ Output to file failed")
                self.failed += 1
                self.errors.append(f"Output to file: {stderr}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting comprehensive jexpand feature tests...")
        print(f"Working directory: {self.workspace}")
        
        start_time = time.time()
        
        # Run all test categories
        self.test_basic_functionality()
        self.test_core_functions()
        self.test_template_filters()
        self.test_compilation_features()
        self.test_operating_modes()
        self.test_output_formats()
        self.test_cli_features()
        
        end_time = time.time()
        
        # Print summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"⏱️  Duration: {end_time - start_time:.2f} seconds")
        
        if self.errors:
            print(f"\n🔥 ERRORS ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                print(f"{i}. {error}")
        
        if self.failed == 0:
            print("\n🎉 ALL TESTS PASSED!")
            return True
        else:
            print(f"\n💥 {self.failed} TESTS FAILED")
            return False

def main():
    """Main entry point"""
    runner = TestRunner()
    success = runner.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()