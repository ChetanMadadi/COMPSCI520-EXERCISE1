#!/usr/bin/env python3
"""
Create APPS-style problems manually
"""

import os
import json

def create_problem_folder(problem_id, problem_data, base_dir="apps_problems"):
    """Create a folder for a single APPS problem."""
    os.makedirs(base_dir, exist_ok=True)
    
    problem_folder = os.path.join(base_dir, f"problem_{problem_id:03d}")
    os.makedirs(problem_folder, exist_ok=True)
    
    # Save problem description
    with open(os.path.join(problem_folder, "problem.txt"), "w") as f:
        f.write(problem_data['description'])
    
    # Save test cases
    with open(os.path.join(problem_folder, "test_cases.json"), "w") as f:
        json.dump(problem_data['test_cases'], f, indent=2)
    
    # Save metadata
    with open(os.path.join(problem_folder, "metadata.json"), "w") as f:
        json.dump(problem_data['metadata'], f, indent=2)
    
    print(f"✓ Created {problem_folder}")
    return problem_folder

def main():
    # Define 5 APPS-style problems
    problems = [
        {
            'description': '''Problem: Sum of Two Numbers

Write a program that reads two integers from standard input and prints their sum.

Input Format:
Two integers on separate lines

Output Format:
A single integer representing the sum

Example:
Input:
5
3

Output:
8
''',
            'test_cases': {
                'inputs': ['5\n3\n', '10\n20\n', '0\n0\n', '-5\n5\n', '100\n200\n'],
                'outputs': ['8\n', '30\n', '0\n', '0\n', '300\n']
            },
            'metadata': {
                'problem_id': 'APPS_001',
                'difficulty': 'introductory',
                'topic': 'basic_io'
            }
        },
        {
            'description': '''Problem: Reverse a String

Write a program that reads a string from standard input and prints it in reverse.

Input Format:
A single line containing a string

Output Format:
The reversed string

Example:
Input:
hello

Output:
olleh
''',
            'test_cases': {
                'inputs': ['hello\n', 'world\n', 'a\n', 'racecar\n', 'Python\n'],
                'outputs': ['olleh\n', 'dlrow\n', 'a\n', 'racecar\n', 'nohtyP\n']
            },
            'metadata': {
                'problem_id': 'APPS_002',
                'difficulty': 'introductory',
                'topic': 'strings'
            }
        },
        {
            'description': '''Problem: Count Vowels

Write a program that reads a string and counts the number of vowels (a, e, i, o, u) in it.
Count both uppercase and lowercase vowels.

Input Format:
A single line containing a string

Output Format:
A single integer representing the count of vowels

Example:
Input:
Hello World

Output:
3
''',
            'test_cases': {
                'inputs': ['Hello World\n', 'aeiou\n', 'xyz\n', 'AEIOU\n', 'Programming\n'],
                'outputs': ['3\n', '5\n', '0\n', '5\n', '3\n']
            },
            'metadata': {
                'problem_id': 'APPS_003',
                'difficulty': 'introductory',
                'topic': 'strings'
            }
        },
        {
            'description': '''Problem: Fibonacci Number

Write a program that reads an integer n and prints the nth Fibonacci number.
The Fibonacci sequence starts with 0, 1, and each subsequent number is the sum of the previous two.
F(0) = 0, F(1) = 1, F(n) = F(n-1) + F(n-2)

Input Format:
A single integer n (0 <= n <= 30)

Output Format:
The nth Fibonacci number

Example:
Input:
6

Output:
8
''',
            'test_cases': {
                'inputs': ['0\n', '1\n', '6\n', '10\n', '15\n'],
                'outputs': ['0\n', '1\n', '8\n', '55\n', '610\n']
            },
            'metadata': {
                'problem_id': 'APPS_004',
                'difficulty': 'interview',
                'topic': 'recursion'
            }
        },
        {
            'description': '''Problem: Prime Number Check

Write a program that reads an integer and determines if it is a prime number.
A prime number is a natural number greater than 1 that has no positive divisors other than 1 and itself.

Input Format:
A single integer n (n >= 2)

Output Format:
Print "YES" if the number is prime, "NO" otherwise

Example:
Input:
7

Output:
YES
''',
            'test_cases': {
                'inputs': ['2\n', '7\n', '10\n', '13\n', '100\n'],
                'outputs': ['YES\n', 'YES\n', 'NO\n', 'YES\n', 'NO\n']
            },
            'metadata': {
                'problem_id': 'APPS_005',
                'difficulty': 'interview',
                'topic': 'mathematics'
            }
        }
    ]
    
    print("Creating APPS-style problems...")
    
    created_folders = []
    for i, problem in enumerate(problems, 1):
        folder = create_problem_folder(i, problem)
        created_folders.append(folder)
    
    # Create README
    with open("apps_problems/README.md", "w") as f:
        f.write("# APPS-Style Problems\n\n")
        f.write("This directory contains programming problems in APPS format.\n\n")
        f.write("## Structure\n\n")
        f.write("Each problem folder contains:\n")
        f.write("- `problem.txt`: The problem statement\n")
        f.write("- `test_cases.json`: Input/output test cases\n")
        f.write("- `metadata.json`: Problem metadata\n\n")
        f.write("## Problems\n\n")
        
        for i, problem in enumerate(problems, 1):
            metadata = problem['metadata']
            f.write(f"{i}. **{metadata['problem_id']}** - {metadata['difficulty']} - Topic: {metadata['topic']}\n")
    
    print(f"\n🎉 Successfully created {len(created_folders)} problem folders!")
    print(f"All problems saved in: ./apps_problems/")

if __name__ == "__main__":
    main()
