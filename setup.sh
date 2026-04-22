#!/bin/bash
# Car Wash Management System - Setup Script
# Run this script to set up the application locally

echo "=================================="
echo "Car Wash Management System Setup"
echo "=================================="
echo ""

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed."
    echo "Please install Python 3.9 or newer from: https://www.python.org/downloads/"
    exit 1
fi

echo "✅ Python 3 found"
python3 --version
echo ""

# Create virtual environment (optional but recommended)
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "=================================="
echo "✅ Setup Complete!"
echo "=================================="
echo ""
echo "To run the application:"
echo "  streamlit run app.py"
echo ""
echo "The app will open at: http://localhost:8501"
echo ""
