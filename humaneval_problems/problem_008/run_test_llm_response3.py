#!/usr/bin/env python3
"""
Test runner for problem_008 using llm_response3
"""
import sys
import traceback
from pathlib import Path
import re

def clean_llm_response(code):
    """Clean LLM response to handle common formatting issues."""
    # Remove markdown code blocks
    if "```python" in code:
        # Extract code between ```python and ```
        start = code.find("```python") + 9
        end = code.find("```", start)
        if end != -1:
            code = code[start:end].strip()
        else:
            # If no closing ```, take everything after ```python
            code = code[start:].strip()
    elif "```" in code:
        # Handle generic code blocks
        start = code.find("```") + 3
        end = code.find("```", start)
        if end != -1:
            code = code[start:end].strip()
        else:
            code = code[start:].strip()
    
    # Fix indentation issues - ensure function body is properly indented
    lines = code.split('\n')
    if lines and lines[0].strip().startswith('def '):
        # This is a function definition
        fixed_lines = [lines[0]]  # Keep the function definition line as-is
        
        for i, line in enumerate(lines[1:], 1):
            if line.strip():  # Non-empty line
                if not line.startswith('    ') and not line.startswith('\t'):
                    # Line is not indented, add 4 spaces
                    fixed_lines.append('    ' + line.strip())
                else:
                    # Line is already indented
                    fixed_lines.append(line)
            else:
                # Empty line
                fixed_lines.append(line)
        
        code = '\n'.join(fixed_lines)
    
    return code

def run_tests():
    """Run tests for problem_008 using llm_response3"""
    try:
        # Load and execute the LLM response from text file (same directory)
        llm_response_path = Path("llm_response3.txt")
        if not llm_response_path.exists():
            print(f"❌ LLM response file not found: {llm_response_path}")
            return False, [f"File not found: {llm_response_path}"]
            
        with open(llm_response_path, "r") as f:
            llm_code = f.read()
        
        # Clean the LLM response to handle common formatting issues
        llm_code = clean_llm_response(llm_code)
        
        # Create a shared namespace for execution
        namespace = {}
        
        # Execute the LLM code to define the function
        exec(llm_code, namespace)
        
        # Load the test.py file from the same directory
        test_file_path = Path("test.py")
        if not test_file_path.exists():
            print(f"❌ Test file not found: {test_file_path}")
            return False, [f"Test file not found: {test_file_path}"]
        
        with open(test_file_path, "r") as f:
            test_code = f.read()
        
        # Execute the test code to define the check function
        exec(test_code, namespace)
        
        # Run the check function with the entry point function
        try:
            # Get the functions from the shared namespace
            if 'match_parens' in namespace and 'check' in namespace:
                namespace['check'](namespace['match_parens'])
                print("✅ All tests passed!")
                return True, []
            else:
                missing = []
                if 'match_parens' not in namespace:
                    missing.append("Function 'match_parens'")
                if 'check' not in namespace:
                    missing.append("Function 'check'")
                error_msg = f"{', '.join(missing)} not found"
                print(f"❌ {error_msg}")
                return False, [error_msg]
                
        except Exception as e:
            error_msg = f"Test failed: {str(e)}"
            print(f"❌ {error_msg}")
            traceback.print_exc()
            return False, [error_msg]
            
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"❌ {error_msg}")
        traceback.print_exc()
        return False, [error_msg]

if __name__ == "__main__":
    success, failures = run_tests()
    sys.exit(0 if success else 1)
