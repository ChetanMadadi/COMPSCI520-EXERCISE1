#!/bin/bash

echo "🎯 Running HumanEval downloader..."

# Activate virtual environment
source venv/bin/activate

# Run the downloader
python download_humaneval.py

echo ""
echo "🎉 Done! Check the 'humaneval_problems' folder for your downloaded problems."