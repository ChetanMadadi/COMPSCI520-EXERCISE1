import os
import subprocess
import sys
from pathlib import Path

def create_run_test_file(problem_name, llm_response_file):
    """Create a run_test.py file for a specific problem and LLM response."""
    
    # Read metadata to get the entry point (function name)
    metadata_file = Path(problem_name) / "metadata.json"
    if metadata_file.exists():
        import json
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        entry_point = metadata.get('entry_point', 'unknown_function')
    else:
        entry_point = 'unknown_function'
    
    # Build the test content using string formatting to avoid f-string issues
    run_test_content = '''#!/usr/bin/env python3
"""
Test runner for PROBLEM_NAME using LLM_RESPONSE_FILE
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
    lines = code.split('\\n')
    if lines and lines[0].strip().startswith('def '):
        # This is a function definition
        fixed_lines = [lines[0]]  # Keep the function definition line as-is
        
        for i, line in enumerate(lines[1:], 1):
            if line.strip():  # Non-empty line
                if not line.startswith('    ') and not line.startswith('\\t'):
                    # Line is not indented, add 4 spaces
                    fixed_lines.append('    ' + line.strip())
                else:
                    # Line is already indented
                    fixed_lines.append(line)
            else:
                # Empty line
                fixed_lines.append(line)
        
        code = '\\n'.join(fixed_lines)
    
    return code

def run_tests():
    """Run tests for PROBLEM_NAME using LLM_RESPONSE_FILE"""
    try:
        # Load and execute the LLM response from text file (same directory)
        llm_response_path = Path("LLM_RESPONSE_FILE.txt")
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
            if 'ENTRY_POINT' in namespace and 'check' in namespace:
                namespace['check'](namespace['ENTRY_POINT'])
                print("✅ All tests passed!")
                return True, []
            else:
                missing = []
                if 'ENTRY_POINT' not in namespace:
                    missing.append("Function 'ENTRY_POINT'")
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
'''
    
    # Replace placeholders with actual values
    run_test_content = run_test_content.replace('PROBLEM_NAME', problem_name)
    run_test_content = run_test_content.replace('LLM_RESPONSE_FILE', llm_response_file)
    run_test_content = run_test_content.replace('ENTRY_POINT', entry_point)
    
    # Create the test file inside the problem directory
    problem_dir = Path(problem_name)
    run_test_filename = problem_dir / f"run_test_{llm_response_file}.py"
    
    with open(run_test_filename, 'w') as f:
        f.write(run_test_content)
    
    return str(run_test_filename)

def find_problems():
    """Find all problems by looking for problem directories with test.py files."""
    problems = set()
    
    # Look for directories that contain test.py files (HumanEval format)
    for item in Path('.').iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            # Check if directory contains test.py file
            if (item / 'test.py').exists():
                problems.add(item.name)
    
    return list(problems)

def run_test_file(run_test_filename):
    """Run a test file and return results."""
    try:
        # Extract the directory and filename
        test_path = Path(run_test_filename)
        test_dir = test_path.parent
        test_file = test_path.name
        
        # Run the test from within the problem directory
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, text=True, timeout=30, cwd=test_dir)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Test execution timed out"
    except Exception as e:
        return False, "", f"Error running test: {str(e)}"

def main():
    """Main function to generate and run tests for all problems and LLM responses."""
    llm_response_files = ['llm_response1', 'llm_response2', 'llm_response3']
    problems = find_problems()
    
    if not problems:
        print("No problems found. Looking for test_*.py files or problem directories.")
        return
    
    print(f"Found problems: {problems}")
    print(f"Testing with LLM responses: {llm_response_files}")
    print("=" * 60)
    
    results = {}
    
    for problem in problems:
        results[problem] = {}
        print(f"\nTesting problem: {problem}")
        print("-" * 40)
        
        for llm_response in llm_response_files:
            print(f"\nTesting {llm_response} on {problem}:")
            
            # Check if LLM response file exists in the problem directory
            llm_response_path = Path(problem) / f"{llm_response}.txt"
            if not llm_response_path.exists():
                print(f"  ✗ {llm_response_path} not found")
                results[problem][llm_response] = {
                    'passed': False,
                    'reason': f"{llm_response_path} file not found",
                    'stdout': '',
                    'stderr': '',
                    'test_file': 'N/A - LLM response file missing'
                }
                continue
            
            # Create run_test file
            run_test_filename = create_run_test_file(problem, llm_response)
            
            # Run the test
            success, stdout, stderr = run_test_file(run_test_filename)
            
            if success:
                print(f"  ✓ {llm_response} PASSED")
                results[problem][llm_response] = {
                    'passed': True,
                    'reason': 'All tests passed',
                    'stdout': stdout,
                    'stderr': stderr,
                    'test_file': run_test_filename
                }
            else:
                print(f"  ✗ {llm_response} FAILED")
                failure_reason = stderr if stderr else stdout
                results[problem][llm_response] = {
                    'passed': False,
                    'reason': failure_reason,
                    'stdout': stdout,
                    'stderr': stderr,
                    'test_file': run_test_filename
                }
            
            # Always show detailed output for each response
            print(f"    Test file: {run_test_filename}")
            if stdout:
                print(f"    Output: {stdout.strip()}")
            if stderr:
                print(f"    Error: {stderr.strip()}")
            
            # Keep the test file (don't delete it)
    
    # Save detailed results to JSON
    import json
    results_file = "test_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n📄 Detailed results saved to: {results_file}")
    
    # Print individual response summaries
    print("\n" + "=" * 80)
    print("INDIVIDUAL RESPONSE SUMMARIES")
    print("=" * 80)
    
    # Collect stats per response
    response_stats = {}
    for problem, llm_results in results.items():
        for llm_response, result in llm_results.items():
            if llm_response not in response_stats:
                response_stats[llm_response] = {'passed': 0, 'failed': 0, 'total': 0}
            
            response_stats[llm_response]['total'] += 1
            if result['passed']:
                response_stats[llm_response]['passed'] += 1
            else:
                response_stats[llm_response]['failed'] += 1
    
    # Show stats for each response
    for llm_response, stats in response_stats.items():
        pass_rate = (stats['passed'] / stats['total']) * 100 if stats['total'] > 0 else 0
        print(f"\n🤖 {llm_response.upper()}:")
        print(f"  ✅ Passed: {stats['passed']}/{stats['total']} ({pass_rate:.1f}%)")
        print(f"  ❌ Failed: {stats['failed']}/{stats['total']}")
        
        # Show failed problems for this response
        failed_problems = []
        for problem, llm_results in results.items():
            if llm_response in llm_results and not llm_results[llm_response]['passed']:
                failed_problems.append(problem)
        
        if failed_problems:
            print(f"  📋 Failed on: {', '.join(failed_problems)}")
    
    # Print overall summary
    print("\n" + "=" * 80)
    print("OVERALL SUMMARY")
    print("=" * 80)
    
    for problem, llm_results in results.items():
        print(f"\n📁 Problem: {problem}")
        for llm_response, result in llm_results.items():
            status = "✅ PASS" if result['passed'] else "❌ FAIL"
            print(f"  {llm_response}: {status}")
            if not result['passed']:
                # Show first line of error for quick reference
                error_preview = result['reason'].split('\n')[0][:100]
                print(f"    💬 {error_preview}...")
                print(f"    📄 Test file: {result['test_file']}")
    
    # Print test files summary
    print(f"\n📂 Generated test files are kept in the current directory:")
    test_files = [result['test_file'] for problem_results in results.values() 
                  for result in problem_results.values()]
    for test_file in sorted(set(test_files)):
        print(f"  • {test_file}")

if __name__ == "__main__":
    main()
