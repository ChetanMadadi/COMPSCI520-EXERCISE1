#!/usr/bin/env python3
"""
APPS Dataset Downloader
Downloads problems from the APPS dataset and organizes them into folders.
"""

import os
import json
import random
from datasets import load_dataset
from pathlib import Path

def create_apps_problem_folder(problem_data, problem_id, base_dir="apps_problems"):
    """Create a folder for a single APPS problem with all its components."""
    # Create base directory if it doesn't exist
    os.makedirs(base_dir, exist_ok=True)
    
    # Create problem-specific folder
    problem_folder = os.path.join(base_dir, f"problem_{problem_id:03d}")
    os.makedirs(problem_folder, exist_ok=True)
    
    # Extract problem components
    problem_id_str = problem_data.get('problem_id', f'APPS_{problem_id}')
    question = problem_data.get('question', '')
    solutions = problem_data.get('solutions', '')
    input_output = problem_data.get('input_output', '')
    difficulty = problem_data.get('difficulty', 'unknown')
    url = problem_data.get('url', '')
    starter_code = problem_data.get('starter_code', '')
    
    # Save problem description
    with open(os.path.join(problem_folder, "problem.txt"), "w") as f:
        f.write(f"Problem ID: {problem_id_str}\n")
        f.write(f"Difficulty: {difficulty}\n")
        f.write(f"URL: {url}\n")
        f.write(f"\n{'='*80}\n\n")
        f.write(question)
    
    # Save starter code if available
    if starter_code:
        with open(os.path.join(problem_folder, "starter_code.py"), "w") as f:
            f.write(starter_code)
    
    # Save reference solutions
    if solutions:
        try:
            solutions_list = json.loads(solutions)
            for i, solution in enumerate(solutions_list):
                with open(os.path.join(problem_folder, f"solution_{i+1}.py"), "w") as f:
                    f.write(solution)
        except:
            with open(os.path.join(problem_folder, "solution_1.py"), "w") as f:
                f.write(solutions)
    
    # Save test cases
    if input_output:
        try:
            test_cases = json.loads(input_output)
            with open(os.path.join(problem_folder, "test_cases.json"), "w") as f:
                json.dump(test_cases, f, indent=2)
            
            # Create a Python test file
            with open(os.path.join(problem_folder, "test.py"), "w") as f:
                f.write(f'"""\nTest cases for {problem_id_str}\n"""\n\n')
                f.write('import json\n')
                f.write('import sys\n')
                f.write('from io import StringIO\n\n')
                f.write('def run_tests(solution_func):\n')
                f.write('    """Run all test cases for the solution."""\n')
                f.write('    with open("test_cases.json", "r") as f:\n')
                f.write('        test_cases = json.load(f)\n')
                f.write('    \n')
                f.write('    inputs = test_cases.get("inputs", [])\n')
                f.write('    outputs = test_cases.get("outputs", [])\n')
                f.write('    \n')
                f.write('    passed = 0\n')
                f.write('    failed = 0\n')
                f.write('    \n')
                f.write('    for i, (input_data, expected_output) in enumerate(zip(inputs, outputs)):\n')
                f.write('        try:\n')
                f.write('            # Redirect stdin for input\n')
                f.write('            old_stdin = sys.stdin\n')
                f.write('            sys.stdin = StringIO(input_data)\n')
                f.write('            \n')
                f.write('            # Capture stdout\n')
                f.write('            old_stdout = sys.stdout\n')
                f.write('            sys.stdout = StringIO()\n')
                f.write('            \n')
                f.write('            # Run solution\n')
                f.write('            solution_func()\n')
                f.write('            \n')
                f.write('            # Get output\n')
                f.write('            actual_output = sys.stdout.getvalue()\n')
                f.write('            \n')
                f.write('            # Restore stdin/stdout\n')
                f.write('            sys.stdin = old_stdin\n')
                f.write('            sys.stdout = old_stdout\n')
                f.write('            \n')
                f.write('            # Compare outputs\n')
                f.write('            if actual_output.strip() == expected_output.strip():\n')
                f.write('                passed += 1\n')
                f.write('                print(f"✓ Test {i+1} passed")\n')
                f.write('            else:\n')
                f.write('                failed += 1\n')
                f.write('                print(f"✗ Test {i+1} failed")\n')
                f.write('                print(f"  Expected: {expected_output.strip()}")\n')
                f.write('                print(f"  Got: {actual_output.strip()}")\n')
                f.write('        except Exception as e:\n')
                f.write('            failed += 1\n')
                f.write('            print(f"✗ Test {i+1} error: {e}")\n')
                f.write('            sys.stdin = old_stdin\n')
                f.write('            sys.stdout = old_stdout\n')
                f.write('    \n')
                f.write('    print(f"\\nResults: {passed} passed, {failed} failed")\n')
                f.write('    return passed, failed\n')
        except Exception as e:
            print(f"Warning: Could not parse test cases for problem {problem_id}: {e}")
    
    # Save metadata
    metadata = {
        "problem_id": problem_id_str,
        "difficulty": difficulty,
        "url": url,
        "has_starter_code": bool(starter_code),
        "has_solutions": bool(solutions),
        "has_test_cases": bool(input_output)
    }
    with open(os.path.join(problem_folder, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✓ Created folder for {problem_id_str} (Difficulty: {difficulty})")
    return problem_folder

def main():
    print("Loading APPS dataset...")
    
    try:
        # Load the APPS dataset (train split has more problems)
        # Use trust_remote_code=True for datasets with custom loading scripts
        dataset = load_dataset("codeparrot/apps", split="train", trust_remote_code=True)
        print(f"Dataset loaded successfully! Total problems: {len(dataset)}")
        
        # Filter for introductory level problems (easier ones)
        intro_problems = [i for i, p in enumerate(dataset) if p.get('difficulty') == 'introductory']
        interview_problems = [i for i, p in enumerate(dataset) if p.get('difficulty') == 'interview']
        
        print(f"Found {len(intro_problems)} introductory problems")
        print(f"Found {len(interview_problems)} interview problems")
        
        # Select 5 problems (mix of difficulties)
        selected_indices = []
        if len(intro_problems) >= 3:
            selected_indices.extend(random.sample(intro_problems, 3))
        if len(interview_problems) >= 2:
            selected_indices.extend(random.sample(interview_problems, 2))
        
        if len(selected_indices) < 5:
            # If not enough, just take random ones
            selected_indices = random.sample(range(len(dataset)), min(5, len(dataset)))
        
        print(f"\nSelected {len(selected_indices)} problems:")
        for i, idx in enumerate(selected_indices, 1):
            problem = dataset[idx]
            print(f"{i}. {problem.get('problem_id', f'Problem {idx}')} - Difficulty: {problem.get('difficulty', 'unknown')}")
        
        print(f"\nCreating problem folders...")
        
        # Create folders for each selected problem
        created_folders = []
        for i, idx in enumerate(selected_indices, 1):
            problem = dataset[idx]
            folder_path = create_apps_problem_folder(problem, i)
            created_folders.append(folder_path)
        
        print(f"\n🎉 Successfully created {len(created_folders)} problem folders!")
        print(f"All problems saved in: ./apps_problems/")
        
        # Create a summary file
        with open("apps_problems/README.md", "w") as f:
            f.write("# APPS Problems\n\n")
            f.write("This directory contains problems from the APPS (Automated Programming Progress Standard) dataset.\n\n")
            f.write("## Structure\n\n")
            f.write("Each problem folder contains:\n")
            f.write("- `problem.txt`: The problem statement\n")
            f.write("- `starter_code.py`: Starter code (if available)\n")
            f.write("- `solution_*.py`: Reference solutions\n")
            f.write("- `test_cases.json`: Input/output test cases\n")
            f.write("- `test.py`: Python test runner\n")
            f.write("- `metadata.json`: Problem metadata\n\n")
            f.write("## Problems\n\n")
            
            for i, idx in enumerate(selected_indices, 1):
                problem = dataset[idx]
                problem_id = problem.get('problem_id', f'Problem {idx}')
                difficulty = problem.get('difficulty', 'unknown')
                f.write(f"{i}. **{problem_id}** - Difficulty: {difficulty} - `problem_{i:03d}/`\n")
        
        print("📝 Created README.md with problem summary")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure you have internet connection and the 'datasets' package installed.")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
