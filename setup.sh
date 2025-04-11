#!/bin/bash

# Exit on error
set -e

echo "Setting up MediMuse.ai development environment..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3 and try again."
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv .venv

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
if [ -f "requirements.txt" ]; then
    echo "Installing requirements..."
    pip install -r requirements.txt
else
    echo "requirements.txt not found. Creating a basic one..."
    echo "portia-sdk" > requirements.txt
    pip install -r requirements.txt
fi

echo "Setup complete! Virtual environment is activated."
echo "To deactivate the virtual environment, run: deactivate" 