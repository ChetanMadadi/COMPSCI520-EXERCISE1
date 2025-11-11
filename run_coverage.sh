#!/bin/bash

echo "🧪 Running Coverage Analysis..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run ./setup.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Install coverage tools if not already installed
echo "📦 Ensuring pytest-cov is installed..."
pip install -q pytest pytest-cov coverage

# Run coverage tests
python run_coverage_tests.py

echo ""
echo "✅ Coverage analysis complete!"
echo "Check coverage_report.txt for detailed results."
