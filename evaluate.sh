#!/bin/bash

echo "🧪 Running HumanEval LLM Evaluation..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "Please copy .env.example to .env and add your API keys:"
    echo "cp .env.example .env"
    echo "Then edit .env with your API credentials."
    exit 1
fi

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "❌ Virtual environment not found. Run ./setup.sh first."
    exit 1
fi

# Run the evaluator
python evaluate_humaneval.py

echo ""
echo "🎉 Evaluation complete! Check the evaluation_summary.json for results."