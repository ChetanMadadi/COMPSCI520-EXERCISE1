#!/usr/bin/env python3
"""
HumanEval LLM Evaluator
Sends problems to LLM APIs and evaluates the responses.
"""

import os
import json
import time
import subprocess
import tempfile
from pathlib import Path
from dotenv import load_dotenv
import openai
import requests

# Load environment variables
load_dotenv()

class LLMEvaluator:
    def __init__(self):
        self.provider = os.getenv('LLM_PROVIDER', 'openai')
        self.model_name = os.getenv('MODEL_NAME', 'gpt-4o-mini')
        self.setup_client()
    
    def setup_client(self):
        """Setup the appropriate LLM client based on provider."""
        if self.provider == 'openai':
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment variables")
            self.client = openai.OpenAI(api_key=api_key)
        
        elif self.provider == 'gemini':
            api_key = os.getenv('GOOGLE_API_KEY')
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not found in environment variables")
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.client = genai  # Direct module reference

        elif self.provider == 'grok':
            api_key = os.getenv('XAI_API_KEY')
            if not api_key:
                raise ValueError("XAI_API_KEY not found in environment variables")
            import requests
            self.client = lambda prompt: requests.post(
                "https://api.x.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={"model": "grok-beta", "messages": [{"role": "user", "content": prompt}]}
            ).json()

        else:
            raise ValueError(f"Provider {self.provider} not implemented yet")
    
    def create_prompt(self, problem_prompt):
        """Create a prompt for the LLM to solve the coding problem."""
        system_prompt = """You are a Python programming expert. You will be given a coding problem with a function signature and docstring. 

Your task is to implement the function body that satisfies the requirements described in the docstring.

Rules:
1. Only provide the complete function implementation
2. Do not include any explanations, comments, or additional text
3. Make sure your solution handles all edge cases mentioned in the docstring
4. The function should be ready to run as-is

Return only the Python code for the complete function."""
        
        user_prompt = f"""Here is the coding problem to solve:

{problem_prompt}

Implement the function body to satisfy the requirements."""
        
        return system_prompt, user_prompt
    
    def call_llm(self, system_prompt, user_prompt):
        """Make API call to the LLM."""
        try:
            if self.provider == 'openai':
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.1,
                    max_tokens=1000
                )
                return response.choices[0].message.content.strip()

            elif self.provider == 'gemini':
                # Gemini (Google Generative AI)
                model = self.client.GenerativeModel(self.model_name)
                response = model.generate_content(
                    [
                        {"role": "system", "parts": [system_prompt]},
                        {"role": "user", "parts": [user_prompt]},
                    ],
                    generation_config={"temperature": 0.1, "max_output_tokens": 1000}
                )
                return response.text.strip()

            elif self.provider == 'grok':
                # Grok (xAI)
                import requests
                api_key = os.getenv("XAI_API_KEY")
                if not api_key:
                    raise ValueError("XAI_API_KEY not found in environment variables")

                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                data = {
                    "model": self.model_name,  # e.g., "grok-beta"
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 1000
                }

                response = requests.post("https://api.x.ai/v1/chat/completions",
                                        headers=headers, json=data)
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"].strip()

            else:
                raise ValueError(f"Provider {self.provider} not implemented yet")

        except Exception as e:
            return f"API Error: {str(e)}"

    
    def extract_code(self, llm_response):
        """Extract Python code from LLM response."""
        # Remove markdown code blocks if present
        if "```python" in llm_response:
            lower_llm_response = llm_response.lower()
            start = lower_llm_response.find("```python") + len("```python")
            end = lower_llm_response.find("```", start)
            if end != -1:
                return llm_response[start:end].strip()
            return llm_response[start:].strip()
        elif "```" in lower_llm_response:
            start = lower_llm_response.find("```") + 3
            end = lower_llm_response.find("```", start)
            if end != -1:
                return llm_response[start:end].strip()
            return llm_response[start:].strip()
        
        return llm_response.strip()
    
    def run_tests(self, problem_folder):
        """Run the tests for a problem and return results."""
        test_file = os.path.join(problem_folder, "run_test.py")
        
        if not os.path.exists(test_file):
            return {"error": "Test file not found"}
        
        try:
            # Run the test file
            result = subprocess.run(
                ["python", test_file],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=problem_folder
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {"error": "Test execution timed out"}
        except Exception as e:
            return {"error": f"Test execution failed: {str(e)}"}

def evaluate_problem(evaluator, problem_folder):
    """Evaluate a single problem."""
    print(f"\n📁 Processing {os.path.basename(problem_folder)}...")
    
    # Load problem data
    prompt_file = os.path.join(problem_folder, "prompt.py")
    metadata_file = os.path.join(problem_folder, "metadata.json")
    
    if not os.path.exists(prompt_file) or not os.path.exists(metadata_file):
        print(f"❌ Missing files in {problem_folder}")
        return
    
    # Read prompt and metadata
    with open(prompt_file, 'r') as f:
        prompt_content = f.read()
    
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    
    task_id = metadata['task_id']
    print(f"🎯 Task: {task_id}")
    
    # Create LLM prompt
    system_prompt, user_prompt = evaluator.create_prompt(prompt_content)
    
    # Call LLM
    print("🤖 Calling LLM...")
    llm_response = evaluator.call_llm(system_prompt, user_prompt)
    
    # Extract code
    llm_code = evaluator.extract_code(llm_response)
    
    # Save LLM response as text file
    response_file = os.path.join(problem_folder, "llm_response.txt")
    with open(response_file, 'w') as f:
        f.write(llm_code)
    
    # Create a simple test runner that imports the LLM solution and runs the original tests
    entry_point = metadata['entry_point']
    llm_test_file = os.path.join(problem_folder, "run_test.py")
    with open(llm_test_file, 'w') as f:
        f.write(f'"""\nTest runner for {task_id} with LLM solution\n"""\n\n')
        f.write('# Import the LLM solution from text file\n')
        f.write('exec(open("llm_response.txt").read())\n\n')
        f.write('# Import the test function\n')
        f.write('exec(open("test.py").read())\n\n')
        f.write('# Run the test with the correct function name\n')
        f.write(f'check({entry_point})\n')
        f.write('print("✅All tests passed!")\n')
    
    # Run tests
    print("🧪 Running tests...")
    test_results = evaluator.run_tests(problem_folder)
    
    # Save evaluation results
    evaluation = {
        "task_id": task_id,
        "model": evaluator.model_name,
        "provider": evaluator.provider,
        "timestamp": time.time(),
        "llm_response": llm_response,
        "extracted_code": llm_code,
        "test_results": test_results,
        "passed": test_results.get("success", False)
    }
    
    results_file = os.path.join(problem_folder, "evaluation_results.json")
    with open(results_file, 'w') as f:
        json.dump(evaluation, f, indent=2)
    
    # Print results
    if evaluation["passed"]:
        print(f"✅ {task_id}: PASSED")
    else:
        print(f"❌ {task_id}: FAILED")
        if "error" in test_results:
            print(f"   Error: {test_results['error']}")
        elif test_results.get("stderr"):
            print(f"   Error: {test_results['stderr'][:200]}...")
    
    return evaluation

def main():
    print("🚀 Starting HumanEval LLM Evaluation...")
    
    # Check for problems directory
    problems_dir = "humaneval_problems"
    if not os.path.exists(problems_dir):
        print(f"❌ Problems directory '{problems_dir}' not found.")
        print("Run download_humaneval.py first to download problems.")
        return
    
    # Initialize evaluator
    try:
        evaluator = LLMEvaluator()
        print(f"🤖 Using {evaluator.provider} with model {evaluator.model_name}")
    except Exception as e:
        print(f"❌ Failed to initialize LLM client: {e}")
        print("Make sure you have set up your .env file with API keys.")
        return
    
    # Find all problem folders
    problem_folders = []
    for item in os.listdir(problems_dir):
        item_path = os.path.join(problems_dir, item)
        if os.path.isdir(item_path) and item.startswith("problem_"):
            problem_folders.append(item_path)
    
    problem_folders.sort()
    print(f"📊 Found {len(problem_folders)} problems to evaluate")
    
    # Evaluate each problem
    results = []
    passed_count = 0
    
    for problem_folder in problem_folders:
        try:
            result = evaluate_problem(evaluator, problem_folder)
            if result:
                results.append(result)
                if result["passed"]:
                    passed_count += 1
        except Exception as e:
            print(f"❌ Error processing {problem_folder}: {e}")
    
    # Create summary
    summary = {
        "total_problems": len(results),
        "passed": passed_count,
        "failed": len(results) - passed_count,
        "pass_rate": passed_count / len(results) if results else 0,
        "model": evaluator.model_name,
        "provider": evaluator.provider,
        "timestamp": time.time(),
        "results": results
    }
    
    summary_file = os.path.join(problems_dir, "evaluation_summary.json")
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Print final summary
    print(f"\n🎉 Evaluation Complete!")
    print(f"📊 Results: {passed_count}/{len(results)} problems passed")
    print(f"📈 Pass rate: {summary['pass_rate']:.1%}")
    print(f"📄 Detailed results saved to: {summary_file}")

if __name__ == "__main__":
    main()