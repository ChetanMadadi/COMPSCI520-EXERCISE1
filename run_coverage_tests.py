#!/usr/bin/env python3
"""
Coverage Testing Script for HumanEval and APPS Problems
Uses pytest-cov to measure line and branch coverage

Usage:
    python run_coverage_tests.py [test_type]
    
    test_type: 
        1 or original - Use original test files (test.py / test_cases.json)
        2 or llm      - Use LLM test files (test_cases_llm.json)
        both          - Run both test types (default)
"""

import os
import sys
import json
import subprocess
import tempfile
import shutil
from pathlib import Path
import re
import argparse

class CoverageAnalyzer:
    def __init__(self, test_type='both'):
        """
        Initialize coverage analyzer.
        
        Args:
            test_type: 'original', 'llm', or 'both'
        """
        self.results = []
        self.test_type = test_type
    
    def clean_llm_response(self, code):
        """Clean LLM response to handle formatting issues."""
        # Remove markdown code blocks
        if "```python" in code:
            start = code.find("```python") + 9
            end = code.find("```", start)
            if end != -1:
                code = code[start:end].strip()
            else:
                code = code[start:].strip()
        elif "```" in code:
            start = code.find("```") + 3
            end = code.find("```", start)
            if end != -1:
                code = code[start:end].strip()
            else:
                code = code[start:].strip()
        
        # Fix indentation
        lines = code.split('\n')
        if lines and lines[0].strip().startswith('def '):
            fixed_lines = [lines[0]]
            for line in lines[1:]:
                if line.strip():
                    if not line.startswith('    ') and not line.startswith('\t'):
                        fixed_lines.append('    ' + line.strip())
                    else:
                        fixed_lines.append(line)
                else:
                    fixed_lines.append(line)
            code = '\n'.join(fixed_lines)
        
        return code
    
    def _detect_function_based_solution(self, code):
        """Detect if solution is function-based (no main execution) or standalone program."""
        lines = code.strip().split('\n')
        
        # Check if there's any top-level code that's not a function/class definition or import
        has_execution_code = False
        in_function = False
        in_class = False
        
        for line in lines:
            stripped = line.strip()
            
            # Skip empty lines and comments
            if not stripped or stripped.startswith('#'):
                continue
            
            # Track if we're inside a function or class
            if stripped.startswith('def '):
                in_function = True
                continue
            elif stripped.startswith('class '):
                in_class = True
                continue
            
            # Check indentation to see if we're still inside function/class
            if in_function or in_class:
                if line and not line[0].isspace():
                    in_function = False
                    in_class = False
                else:
                    continue
            
            # If we find top-level execution code (not import, not def, not class)
            if not stripped.startswith('import ') and not stripped.startswith('from ') and \
               not stripped.startswith('def ') and not stripped.startswith('class '):
                has_execution_code = True
                break
        
        # If no execution code found, it's function-based
        return not has_execution_code
    
    def _extract_main_function_name(self, code):
        """Extract the name of the main function (first defined function)."""
        lines = code.strip().split('\n')
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('def '):
                # Extract function name
                func_name = stripped[4:].split('(')[0].strip()
                return func_name
        
        return None
    
    def test_humaneval_problem(self, problem_folder, use_llm_tests=False):
        """Test a HumanEval problem with coverage."""
        problem_name = os.path.basename(problem_folder)
        test_suffix = "_llm" if use_llm_tests else ""
        
        # Check for required files
        llm_response_file = os.path.join(problem_folder, "llm_response1.txt")
        test_file = os.path.join(problem_folder, "test.py")
        metadata_file = os.path.join(problem_folder, "metadata.json")
        
        if not all(os.path.exists(f) for f in [llm_response_file, test_file, metadata_file]):
            return None
        
        # Read files
        with open(llm_response_file, 'r') as f:
            llm_code = self.clean_llm_response(f.read())
        
        with open(test_file, 'r') as f:
            test_code = f.read()
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        entry_point = metadata.get('entry_point', 'unknown')
        
        # Load custom test cases if using LLM tests
        custom_tests = None
        llm_test_cases_file = os.path.join(problem_folder, "test_cases_llm.json")
        if use_llm_tests:
            if not os.path.exists(llm_test_cases_file):
                return None
            with open(llm_test_cases_file, 'r') as f:
                custom_tests = json.load(f)
        
        # Create temporary directory for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write solution file
            solution_file = os.path.join(tmpdir, "solution.py")
            with open(solution_file, 'w') as f:
                f.write(llm_code)
            
            # Copy test file to tmpdir
            test_file_copy = os.path.join(tmpdir, "original_test.py")
            shutil.copy(test_file, test_file_copy)
            
            # Create test file
            test_runner = os.path.join(tmpdir, "test_solution.py")
            with open(test_runner, 'w') as f:
                f.write("import sys\n")
                f.write("import pytest\n")
                f.write("import solution\n\n")
                
                if custom_tests:
                    # Add custom test cases
                    f.write("# Custom test cases from test_cases_llm.json\n")
                    test_cases = custom_tests.get('test_cases', [])
                    for i, test_case in enumerate(test_cases):
                        f.write(f"def test_custom_{i}():\n")
                        inputs = test_case.get('input', [])
                        expected = test_case.get('expected', None)
                        f.write(f"    result = solution.{entry_point}({', '.join(map(repr, inputs))})\n")
                        f.write(f"    assert result == {repr(expected)}, f'Expected {{repr({repr(expected)})}}, got {{repr(result)}}'\n\n")
                else:
                    # Use original test code
                    f.write("# Load test code\n")
                    f.write(f"with open('original_test.py', 'r') as f:\n")
                    f.write(f"    test_code = f.read()\n")
                    f.write(f"exec(test_code)\n\n")
                    f.write("# Run test\n")
                    f.write("def test_solution():\n")
                    f.write(f"    check(solution.{entry_point})\n")
            
            # Run pytest with coverage and verbose output
            result = subprocess.run(
                [sys.executable, '-m', 'pytest', '--cov=solution', '--cov-report=json', 
                 '--cov-branch', '-v', '--tb=line', 'test_solution.py'],
                cwd=tmpdir,
                capture_output=True,
                text=True
            )
            
            # Count individual test results from pytest output
            passed_tests = result.stdout.count(' PASSED')
            failed_tests = result.stdout.count(' FAILED')
            total_tests = passed_tests + failed_tests
            
            # If using custom tests, we have individual test functions
            # If using original tests, count assertions from error output
            if custom_tests:
                test_status = f'{passed_tests}/{total_tests}' if total_tests > 0 else 'Error'
            else:
                # For original tests, check if the single test passed
                tests_passed = result.returncode == 0
                # Try to count assertions from the test file
                if tests_passed:
                    test_status = 'All Pass'
                else:
                    # Count how many assertions were in the test
                    test_file_copy_path = os.path.join(tmpdir, 'original_test.py')
                    if os.path.exists(test_file_copy_path):
                        with open(test_file_copy_path, 'r') as tf:
                            test_content = tf.read()
                            assertion_count = test_content.count('assert ')
                            # We don't know exactly how many passed, but we know it failed
                            test_status = f'0/{assertion_count}' if assertion_count > 0 else 'Fail'
                    else:
                        test_status = 'Fail'
            
            # Debug: print errors if any
            if result.returncode != 0 and result.stderr:
                print(f"\n  Debug - pytest error: {result.stderr[:200]}")
            
            # Parse coverage results
            coverage_file = os.path.join(tmpdir, 'coverage.json')
            if os.path.exists(coverage_file):
                with open(coverage_file, 'r') as f:
                    coverage_data = json.load(f)
                
                # Extract coverage metrics
                files = coverage_data.get('files', {})
                solution_coverage = files.get('solution.py', {})
                
                line_coverage = solution_coverage.get('summary', {}).get('percent_covered', 0)
                num_statements = solution_coverage.get('summary', {}).get('num_statements', 0)
                covered_lines = solution_coverage.get('summary', {}).get('covered_lines', 0)
                missing_lines = solution_coverage.get('summary', {}).get('missing_lines', 0)
                
                # Branch coverage
                num_branches = solution_coverage.get('summary', {}).get('num_branches', 0)
                covered_branches = solution_coverage.get('summary', {}).get('covered_branches', 0)
                branch_coverage = (covered_branches / num_branches * 100) if num_branches > 0 else 100
                
                # Determine overall test result
                tests_passed = result.returncode == 0
                
                # Interpretation
                interpretation = self.interpret_coverage(line_coverage, branch_coverage, 
                                                        num_branches, tests_passed)
                
                test_type = "LLM Tests" if use_llm_tests else "Original"
                return {
                    'problem': problem_name + test_suffix,
                    'type': f'HumanEval ({test_type})',
                    'tests_passed': test_status,
                    'line_coverage': round(line_coverage, 1),
                    'branch_coverage': round(branch_coverage, 1) if num_branches > 0 else 'N/A',
                    'num_statements': num_statements,
                    'covered_lines': covered_lines,
                    'missing_lines': missing_lines,
                    'num_branches': num_branches,
                    'covered_branches': covered_branches,
                    'interpretation': interpretation
                }
            else:
                test_type = "LLM Tests" if use_llm_tests else "Original"
                return {
                    'problem': problem_name + test_suffix,
                    'type': f'HumanEval ({test_type})',
                    'tests_passed': '0/0 (Error)',
                    'line_coverage': 0,
                    'branch_coverage': 'N/A',
                    'interpretation': 'Coverage data not generated'
                }
    
    def test_apps_problem(self, problem_folder, use_llm_tests=False):
        """Test an APPS problem with coverage."""
        problem_name = os.path.basename(problem_folder)
        test_suffix = "_llm" if use_llm_tests else ""
        
        # Check for required files
        llm_response_file = os.path.join(problem_folder, "llm_response1.txt")
        test_cases_file = os.path.join(problem_folder, "test_cases.json")
        llm_test_cases_file = os.path.join(problem_folder, "test_cases_llm.json")
        
        # Choose which test file to use
        if use_llm_tests:
            if not os.path.exists(llm_test_cases_file):
                return None
            test_cases_file = llm_test_cases_file
        
        if not all(os.path.exists(f) for f in [llm_response_file, test_cases_file]):
            return None
        
        # Read files
        with open(llm_response_file, 'r') as f:
            llm_code = self.clean_llm_response(f.read())
        
        with open(test_cases_file, 'r') as f:
            test_cases = json.load(f)
        
        inputs = test_cases.get('inputs', [])
        outputs = test_cases.get('outputs', [])
        
        # Detect if solution is function-based or standalone program
        is_function_based = self._detect_function_based_solution(llm_code)
        
        # Create temporary directory for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            # Prepare solution code
            solution_code = llm_code
            
            # If function-based, add wrapper code to call the function
            if is_function_based:
                main_func = self._extract_main_function_name(llm_code)
                if main_func:
                    solution_code += f"\n\n# Auto-generated wrapper\n"
                    solution_code += f"def _run_solution():\n"
                    solution_code += f"    result = {main_func}()\n"
                    solution_code += f"    if result is not None:\n"
                    solution_code += f"        print(result)\n"
            
            # Write solution file
            solution_file = os.path.join(tmpdir, "solution.py")
            with open(solution_file, 'w') as f:
                f.write(solution_code)
            
            # Create test file
            test_runner = os.path.join(tmpdir, "test_solution.py")
            with open(test_runner, 'w') as f:
                f.write("import sys\n")
                f.write("import pytest\n")
                f.write("from io import StringIO\n")
                f.write("import importlib\n\n")
                
                # Create test cases
                for i, (input_data, expected_output) in enumerate(zip(inputs, outputs)):
                    f.write(f"def test_case_{i}():\n")
                    f.write(f"    import solution\n")
                    f.write(f"    importlib.reload(solution)\n")
                    f.write(f"    \n")
                    f.write(f"    old_stdin = sys.stdin\n")
                    f.write(f"    old_stdout = sys.stdout\n")
                    f.write(f"    try:\n")
                    f.write(f"        sys.stdin = StringIO({repr(input_data)})\n")
                    f.write(f"        sys.stdout = StringIO()\n")
                    f.write(f"        \n")
                    if is_function_based:
                        f.write(f"        # Call the wrapper function\n")
                        f.write(f"        solution._run_solution()\n")
                    else:
                        f.write(f"        # Execute module-level code\n")
                        f.write(f"        with open('solution.py', 'r') as file:\n")
                        f.write(f"            exec(file.read(), solution.__dict__)\n")
                    f.write(f"        \n")
                    f.write(f"        output = sys.stdout.getvalue()\n")
                    expected_repr = repr(expected_output.strip())
                    f.write(f"        expected = {expected_repr}\n")
                    f.write(f"        assert output.strip() == expected, f'Expected {{expected!r}}, got {{output.strip()!r}}'\n")
                    f.write(f"    finally:\n")
                    f.write(f"        sys.stdin = old_stdin\n")
                    f.write(f"        sys.stdout = old_stdout\n\n")
            
            # Run pytest with coverage
            result = subprocess.run(
                [sys.executable, '-m', 'pytest', '--cov=solution', '--cov-report=json', 
                 '--cov-branch', '-v', 'test_solution.py'],
                cwd=tmpdir,
                capture_output=True,
                text=True
            )
            
            # Debug: print errors if any
            if result.returncode != 0 and result.stderr:
                print(f"\n  Debug - pytest error: {result.stderr[:200]}")
            
            # Count passed tests
            passed_tests = result.stdout.count(' PASSED')
            total_tests = len(inputs)
            
            # Parse coverage results
            coverage_file = os.path.join(tmpdir, 'coverage.json')
            if os.path.exists(coverage_file):
                with open(coverage_file, 'r') as f:
                    coverage_data = json.load(f)
                
                files = coverage_data.get('files', {})
                solution_coverage = files.get('solution.py', {})
                
                line_coverage = solution_coverage.get('summary', {}).get('percent_covered', 0)
                num_statements = solution_coverage.get('summary', {}).get('num_statements', 0)
                covered_lines = solution_coverage.get('summary', {}).get('covered_lines', 0)
                missing_lines = solution_coverage.get('summary', {}).get('missing_lines', 0)
                
                num_branches = solution_coverage.get('summary', {}).get('num_branches', 0)
                covered_branches = solution_coverage.get('summary', {}).get('covered_branches', 0)
                branch_coverage = (covered_branches / num_branches * 100) if num_branches > 0 else 100
                
                tests_passed = result.returncode == 0
                
                interpretation = self.interpret_coverage(line_coverage, branch_coverage, 
                                                        num_branches, tests_passed)
                
                test_type = "LLM Tests" if use_llm_tests else "Original"
                return {
                    'problem': problem_name + test_suffix,
                    'type': f'APPS ({test_type})',
                    'tests_passed': f'{passed_tests}/{total_tests}',
                    'line_coverage': round(line_coverage, 1),
                    'branch_coverage': round(branch_coverage, 1) if num_branches > 0 else 'N/A',
                    'num_statements': num_statements,
                    'covered_lines': covered_lines,
                    'missing_lines': missing_lines,
                    'num_branches': num_branches,
                    'covered_branches': covered_branches,
                    'interpretation': interpretation
                }
            else:
                test_type = "LLM Tests" if use_llm_tests else "Original"
                return {
                    'problem': problem_name + test_suffix,
                    'type': f'APPS ({test_type})',
                    'tests_passed': f'{passed_tests}/{total_tests}',
                    'line_coverage': 0,
                    'branch_coverage': 'N/A',
                    'interpretation': 'Coverage data not generated'
                }
    
    def interpret_coverage(self, line_cov, branch_cov, num_branches, tests_passed):
        """Generate interpretation of coverage results."""
        if not tests_passed:
            return "Tests failed - coverage may be incomplete"
        
        if line_cov == 100 and (branch_cov == 100 or num_branches == 0):
            return "Perfect coverage - all code paths tested"
        elif line_cov >= 90:
            if isinstance(branch_cov, (int, float)) and branch_cov < 80:
                return "High line coverage but low branch coverage - missing edge cases"
            return "Excellent coverage"
        elif line_cov >= 70:
            if isinstance(branch_cov, (int, float)) and branch_cov < 60:
                return "Good line coverage but poor branch coverage - untested conditionals"
            return "Good coverage with room for improvement"
        elif line_cov >= 50:
            return "Moderate coverage - significant untested code paths"
        else:
            return "Low coverage - many code paths untested"
    
    def run_all_tests(self):
        """Run coverage tests for all problems based on test_type."""
        print(f"🧪 Running Coverage Tests (Test Type: {self.test_type})...\n")
        
        run_original = self.test_type in ['original', 'both']
        run_llm = self.test_type in ['llm', 'both']
        
        # Test HumanEval problems
        humaneval_dir = "humaneval_problems"
        if os.path.exists(humaneval_dir):
            if run_original:
                print("Testing HumanEval problems (Original Tests)...")
                for item in sorted(os.listdir(humaneval_dir)):
                    item_path = os.path.join(humaneval_dir, item)
                    if os.path.isdir(item_path) and item.startswith("problem_"):
                        print(f"  Testing {item}...", end=" ")
                        result = self.test_humaneval_problem(item_path, use_llm_tests=False)
                        if result:
                            self.results.append(result)
                            print("✓")
                        else:
                            print("⊘ (missing files)")
            
            if run_llm:
                print("\nTesting HumanEval problems (LLM Test Cases)...")
                found_llm_tests = False
                for item in sorted(os.listdir(humaneval_dir)):
                    item_path = os.path.join(humaneval_dir, item)
                    if os.path.isdir(item_path) and item.startswith("problem_"):
                        llm_test_file = os.path.join(item_path, "test_cases_llm.json")
                        if os.path.exists(llm_test_file):
                            found_llm_tests = True
                            print(f"  Testing {item}...", end=" ")
                            result = self.test_humaneval_problem(item_path, use_llm_tests=True)
                            if result:
                                self.results.append(result)
                                print("✓")
                            else:
                                print("⊘ (error)")
                if not found_llm_tests:
                    print("  No LLM test files found (test_cases_llm.json)")
        
        # Test APPS problems
        apps_dir = "apps_problems"
        if os.path.exists(apps_dir):
            if run_original:
                print("\nTesting APPS problems (Original Tests)...")
                for item in sorted(os.listdir(apps_dir)):
                    item_path = os.path.join(apps_dir, item)
                    if os.path.isdir(item_path) and item.startswith("problem_"):
                        print(f"  Testing {item}...", end=" ")
                        result = self.test_apps_problem(item_path, use_llm_tests=False)
                        if result:
                            self.results.append(result)
                            print("✓")
                        else:
                            print("⊘ (missing files)")
            
            if run_llm:
                print("\nTesting APPS problems (LLM Test Cases)...")
                found_llm_tests = False
                for item in sorted(os.listdir(apps_dir)):
                    item_path = os.path.join(apps_dir, item)
                    if os.path.isdir(item_path) and item.startswith("problem_"):
                        llm_test_file = os.path.join(item_path, "test_cases_llm.json")
                        if os.path.exists(llm_test_file):
                            found_llm_tests = True
                            print(f"  Testing {item}...", end=" ")
                            result = self.test_apps_problem(item_path, use_llm_tests=True)
                            if result:
                                self.results.append(result)
                                print("✓")
                            else:
                                print("⊘ (error)")
                if not found_llm_tests:
                    print("  No LLM test files found (test_cases_llm.json)")
    
    def generate_report(self):
        """Generate comprehensive coverage report."""
        if not self.results:
            print("\n❌ No results to report")
            return
        
        print("\n" + "="*120)
        print("COVERAGE ANALYSIS REPORT")
        print("="*120)
        
        # Detailed results
        print("\nDETAILED RESULTS:")
        print("-"*120)
        print(f"{'Problem':<20} {'Type':<20} {'Tests':<15} {'Line %':<10} {'Branch %':<12}")
        print("-"*120)
        
        for result in self.results:
            branch_str = str(result['branch_coverage']) if result['branch_coverage'] != 'N/A' else 'N/A'
            print(f"{result['problem']:<20} {result['type']:<20} {result['tests_passed']:<15} "
                  f"{result['line_coverage']:<10.1f} {branch_str:<12}")
        
        # Summary statistics
        print("\n" + "="*120)
        print("SUMMARY STATISTICS")
        print("="*120)
        
        humaneval_results = [r for r in self.results if r['type'] == 'HumanEval']
        apps_results = [r for r in self.results if r['type'] == 'APPS']
        
        if humaneval_results:
            avg_line = sum(r['line_coverage'] for r in humaneval_results) / len(humaneval_results)
            branch_vals = [r['branch_coverage'] for r in humaneval_results if isinstance(r['branch_coverage'], (int, float))]
            avg_branch = sum(branch_vals) / len(branch_vals) if branch_vals else 0
            
            print(f"\nHumanEval Problems ({len(humaneval_results)} problems):")
            print(f"  Average Line Coverage: {avg_line:.1f}%")
            print(f"  Average Branch Coverage: {avg_branch:.1f}%")
        
        if apps_results:
            avg_line = sum(r['line_coverage'] for r in apps_results) / len(apps_results)
            branch_vals = [r['branch_coverage'] for r in apps_results if isinstance(r['branch_coverage'], (int, float))]
            avg_branch = sum(branch_vals) / len(branch_vals) if branch_vals else 0
            
            print(f"\nAPPS Problems ({len(apps_results)} problems):")
            print(f"  Average Line Coverage: {avg_line:.1f}%")
            print(f"  Average Branch Coverage: {avg_branch:.1f}%")
        
        # Save to file
        with open("coverage_report.txt", "w") as f:
            f.write("COVERAGE ANALYSIS REPORT\n")
            f.write("="*120 + "\n\n")
            f.write(f"{'Problem':<20} {'Type':<20} {'Tests':<15} {'Line %':<10} {'Branch %':<12}\n")
            f.write("-"*120 + "\n")
            
            for result in self.results:
                branch_str = str(result['branch_coverage']) if result['branch_coverage'] != 'N/A' else 'N/A'
                f.write(f"{result['problem']:<20} {result['type']:<20} {result['tests_passed']:<15} "
                       f"{result['line_coverage']:<10.1f} {branch_str:<12}\n")
        
        print("\n📄 Report saved to: coverage_report.txt")

def main():
    parser = argparse.ArgumentParser(
        description='Run coverage tests on HumanEval and APPS problems',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python run_coverage_tests.py                    # Run both test types
  python run_coverage_tests.py 1                  # Run original tests only
  python run_coverage_tests.py 2                  # Run LLM tests only
  python run_coverage_tests.py original           # Run original tests only
  python run_coverage_tests.py llm                # Run LLM tests only
  python run_coverage_tests.py both               # Run both test types
        '''
    )
    
    parser.add_argument(
        'test_type',
        nargs='?',
        default='both',
        choices=['1', '2', 'original', 'llm', 'both'],
        help='Test type to run: 1/original (original tests), 2/llm (LLM tests), both (default)'
    )
    
    args = parser.parse_args()
    
    # Map numeric choices to names
    test_type_map = {
        '1': 'original',
        '2': 'llm',
        'original': 'original',
        'llm': 'llm',
        'both': 'both'
    }
    
    test_type = test_type_map[args.test_type]
    
    print(f"Test Type Selected: {test_type.upper()}")
    print("="*60)
    
    analyzer = CoverageAnalyzer(test_type=test_type)
    analyzer.run_all_tests()
    analyzer.generate_report()

if __name__ == "__main__":
    main()
