#!/bin/bash
# Development environment setup

echo "Setting up development environment..."

# Create virtual environment
python -m venv venv

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements-dev.txt

# Install package in development mode
pip install -e .

echo "Development environment ready!"
echo "Activate it with: source venv/bin/activate (or venv\\Scripts\\activate on Windows)"
