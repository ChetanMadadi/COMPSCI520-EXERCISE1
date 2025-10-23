#!/usr/bin/env python3
"""
HumanEval Dataset Downloader
Downloads N random problems from the HumanEval dataset and organizes them into folders.
"""

import os
import random
from datasets import load_dataset
import json

def create_problem_folder(problem_data, problem_id, base_dir="humaneval_problems"):
    """Create a folder for a single problem with all its components."""
    # Create base directory if it doesn't exist
    os.makedirs(base_dir, exist_ok=True)
    
    # Create problem-specific folder
    problem_folder = os.path.join(base_dir, f"problem_{problem_id:03d}")
    os.makedirs(problem_folder, exist_ok=True)
    
    # Extract problem components
    task_id = problem_data['task_id']
    prompt = problem_data['prompt']
    canonical_solution = problem_data['canonical_solution']
    test = problem_data['test']
    entry_point = problem_data['entry_point']
    
    # Save prompt
    with open(os.path.join(problem_folder, "prompt.py"), "w") as f:
        f.write(f'"""\nTask ID: {task_id}\nEntry Point: {entry_point}\n"""\n\n')
        f.write(prompt)
    
    # Save reference solution
    with open(os.path.join(problem_folder, "solution.py"), "w") as f:
        f.write(f'"""\nReference Solution for {task_id}\n"""\n\n')
        f.write(prompt + canonical_solution)
    
    # Save tests
    with open(os.path.join(problem_folder, "test.py"), "w") as f:
        f.write(f'"""\nTests for {task_id}\n"""\n\n')
        # f.write(prompt + canonical_solution + "\n\n" + test)
        f.write(test)

    # Save metadata as JSON
    metadata = {
        "task_id": task_id,
        "entry_point": entry_point,
        "problem_number": problem_id
    }
    with open(os.path.join(problem_folder, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✓ Created folder for {task_id}")
    return problem_folder

def main():
    print("Loading HumanEval dataset...")
    
    try:
        # Load the HumanEval dataset
        dataset = load_dataset("openai_humaneval", split="test")
        print(f"Dataset loaded successfully! Total problems: {len(dataset)}")
        
        # Select N random problems
        total_problems = len(dataset)
        NUM_PROB = 20
        random_indices = random.sample(range(total_problems), min(NUM_PROB, total_problems))
        
        print(f"\nSelected {len(random_indices)} random problems:")
        for i, idx in enumerate(random_indices, 1):
            problem = dataset[idx]
            print(f"{i}. {problem['task_id']}")
        
        print(f"\nCreating problem folders...")
        
        # Create folders for each selected problem
        created_folders = []
        for i, idx in enumerate(random_indices, 1):
            problem = dataset[idx]
            folder_path = create_problem_folder(problem, i)
            created_folders.append(folder_path)
        
        print(f"\n🎉 Successfully created {len(created_folders)} problem folders!")
        print(f"All problems saved in: ./humaneval_problems/")
        
        # Create a summary file
        with open("humaneval_problems/README.md", "w") as f:
            f.write("# HumanEval Problems\n\n")
            f.write("This directory contains "+str(len(created_folders))+" randomly selected problems from the HumanEval dataset.\n\n")
            f.write("## Structure\n\n")
            f.write("Each problem folder contains:\n")
            f.write("- `prompt.py`: The problem statement and function signature\n")
            f.write("- `solution.py`: The complete problem with reference solution\n")
            f.write("- `test.py`: The problem, solution, and test cases\n")
            f.write("- `metadata.json`: Problem metadata\n\n")
            f.write("## Problems\n\n")
            
            for i, idx in enumerate(random_indices, 1):
                problem = dataset[idx]
                f.write(f"{i}. **{problem['task_id']}** - `problem_{i:03d}/`\n")
        
        print("📝 Created README.md with problem summary")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure you have internet connection and the 'datasets' package installed.")
        print("Run: pip install datasets")

if __name__ == "__main__":
    main()