#!/bin/bash

echo "🧪 HumanEval LLM Response Testing Suite"
echo "======================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run ./setup.sh first."
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if setup_test.py exists
if [ ! -f "setup_test.py" ]; then
    echo "❌ setup_test.py not found!"
    exit 1
fi

# Check if humaneval_problems directory exists
if [ ! -d "humaneval_problems" ]; then
    echo "❌ humaneval_problems directory not found!"
    echo "Run ./run.sh first to download problems."
    exit 1
fi

# Count available problems
problem_count=$(find humaneval_problems -name "problem_*" -type d | wc -l)
echo "📊 Found $problem_count problems in humaneval_problems/"

# Count available LLM response files
response_count=0
for i in {1..3}; do
    if find humaneval_problems -name "llm_response${i}.txt" | grep -q .; then
        response_count=$((response_count + 1))
    fi
done

echo "🤖 Found LLM response files for response variants: $response_count/3"

if [ $response_count -eq 0 ]; then
    echo "❌ No llm_response*.txt files found!"
    echo "Make sure you have llm_response1.txt, llm_response2.txt, etc. in your problem folders."
    exit 1
fi

echo ""
echo "🚀 Starting test generation and execution..."
echo "This will:"
echo "  1. Generate test runners for each problem and LLM response combination"
echo "  2. Execute all tests and collect results"
echo "  3. Display a summary of pass/fail rates"
echo ""

# Change to humaneval_problems directory to run tests
cd humaneval_problems

# Run the test setup and execution
echo "📝 Generating and running tests..."
python ../setup_test.py

# Check the exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Test execution completed successfully!"
else
    echo ""
    echo "❌ Test execution encountered errors."
    echo "Check the output above for details."
fi

# Return to original directory
cd ..

echo ""
echo "🎉 Testing complete!"
echo "Check the output above for detailed results."