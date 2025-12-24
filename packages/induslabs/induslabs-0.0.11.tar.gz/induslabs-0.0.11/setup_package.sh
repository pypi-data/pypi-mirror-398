#!/bin/bash
# Setup script for IndusLabs Python SDK package

set -e

echo "========================================"
echo "IndusLabs SDK - Package Setup Script"
echo "========================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create directory structure
echo -e "${BLUE}Creating directory structure...${NC}"
mkdir -p induslabs
mkdir -p tests
mkdir -p examples
mkdir -p .github/workflows

# Create __init__ files
echo -e "${BLUE}Creating __init__.py files...${NC}"

cat > induslabs/__init__.py << 'EOF'
"""IndusLabs Voice API SDK."""

from .client import (
    Client,
    TTS,
    STT,
    TTSResponse,
    TTSStreamResponse,
    AsyncTTSStreamResponse,
    STTResponse,
)

__version__ = "0.0.1"
__all__ = [
    "Client",
    "TTS",
    "STT",
    "TTSResponse",
    "TTSStreamResponse",
    "AsyncTTSStreamResponse",
    "STTResponse",
]
EOF

cat > tests/__init__.py << 'EOF'
"""Tests for IndusLabs SDK."""
EOF

# Create MANIFEST.in
echo -e "${BLUE}Creating MANIFEST.in...${NC}"
cat > MANIFEST.in << 'EOF'
include README.md
include LICENSE
recursive-include examples *.py
recursive-include tests *.py
EOF

# Create .gitignore
echo -e "${BLUE}Creating .gitignore...${NC}"
cat > .gitignore << 'EOF'
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# PyInstaller
*.manifest
*.spec

# Unit test / coverage reports
htmlcov/
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.pytest_cache/

# Virtual environments
venv/
ENV/
env/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Audio files (for testing)
*.wav
*.mp3
*.pcm

# PyPI config
.pypirc
EOF

# Create requirements files
echo -e "${BLUE}Creating requirements.txt...${NC}"
cat > requirements.txt << 'EOF'
requests>=2.25.0
aiohttp>=3.8.0
EOF

cat > requirements-dev.txt << 'EOF'
-r requirements.txt
pytest>=7.0.0
pytest-asyncio>=0.21.0
black>=22.0.0
flake8>=4.0.0
mypy>=0.950
twine>=4.0.0
build>=0.10.0
EOF

# Create pytest configuration
echo -e "${BLUE}Creating pytest.ini...${NC}"
cat > pytest.ini << 'EOF'
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
asyncio_mode = auto
EOF

# Create GitHub Actions workflow
echo -e "${BLUE}Creating GitHub Actions workflow...${NC}"
cat > .github/workflows/tests.yml << 'EOF'
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ['3.7', '3.8', '3.9', '3.10', '3.11']
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements-dev.txt
    
    - name: Run tests
      run: pytest
    
    - name: Check code formatting
      run: black --check induslabs/
    
    - name: Lint
      run: flake8 induslabs/ --max-line-length=100
EOF

cat > .github/workflows/publish.yml << 'EOF'
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.x'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine
    
    - name: Build package
      run: python -m build
    
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: twine upload dist/*
EOF

# Create development setup script
echo -e "${BLUE}Creating dev-setup.sh...${NC}"
cat > dev-setup.sh << 'EOF'
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
EOF

chmod +x dev-setup.sh

# Create build script
echo -e "${BLUE}Creating build.sh...${NC}"
cat > build.sh << 'EOF'
#!/bin/bash
# Build script for the package

set -e

echo "Cleaning previous builds..."
rm -rf build/ dist/ *.egg-info

echo "Running tests..."
pytest

echo "Checking code format..."
black --check induslabs/

echo "Building package..."
python -m build

echo "Checking distribution..."
twine check dist/*

echo ""
echo "Build complete! Distribution files:"
ls -lh dist/

echo ""
echo "To upload to Test PyPI:"
echo "  twine upload --repository testpypi dist/*"
echo ""
echo "To upload to PyPI:"
echo "  twine upload dist/*"
EOF

chmod +x build.sh

# Create quick test script
echo -e "${BLUE}Creating quick-test.sh...${NC}"
cat > quick-test.sh << 'EOF'
#!/bin/bash
# Quick test script

echo "Running quick tests..."

# Test imports
python -c "from induslabs import Client, TTS, STT; print('✓ Imports successful')"

# Run unit tests
pytest -v

echo ""
echo "✓ All tests passed!"
EOF

chmod +x quick-test.sh

# Summary
echo ""
echo -e "${GREEN}========================================"
echo "Setup Complete!"
echo -e "========================================${NC}"
echo ""
echo "Directory structure created:"
echo "  ✓ induslabs/"
echo "  ✓ tests/"
echo "  ✓ examples/"
echo "  ✓ .github/workflows/"
echo ""
echo "Files created:"
echo "  ✓ __init__.py files"
echo "  ✓ MANIFEST.in"
echo "  ✓ .gitignore"
echo "  ✓ requirements.txt"
echo "  ✓ requirements-dev.txt"
echo "  ✓ pytest.ini"
echo "  ✓ GitHub Actions workflows"
echo "  ✓ Helper scripts"
echo ""
echo "Next steps:"
echo "  1. Copy client.py to induslabs/client.py"
echo "  2. Copy setup.py and pyproject.toml to root"
echo "  3. Copy README.md and LICENSE to root"
echo "  4. Copy test files to tests/"
echo "  5. Copy example files to examples/"
echo "  6. Run: ./dev-setup.sh"
echo "  7. Run: ./quick-test.sh"
echo "  8. Run: ./build.sh"
echo ""
echo "To publish:"
echo "  - Test: twine upload --repository testpypi dist/*"
echo "  - Prod: twine upload dist/*"
echo ""