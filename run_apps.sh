#!/bin/bash

echo "🚀 Downloading APPS problems..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run ./setup.sh first."
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Run the downloader
python download_apps.py

echo ""
echo "🎉 Done! Check the 'apps_problems' folder for your downloaded problems."
