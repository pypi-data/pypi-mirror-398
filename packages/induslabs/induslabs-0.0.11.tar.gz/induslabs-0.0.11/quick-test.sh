#!/bin/bash
# Quick test script

echo "Running quick tests..."

# Test imports
python -c "from induslabs import Client, TTS, STT; print('✓ Imports successful')"

# Run unit tests
pytest -v

echo ""
echo "✓ All tests passed!"
