#!/bin/bash
# VALLUM — Automated Setup Script

set -e

echo "VALLUM — Setup Starting..."
echo ""

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check Python
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.11"
echo "Checking Python version..."
if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}Python $REQUIRED_VERSION+ required. Found: $PYTHON_VERSION${NC}"
    exit 1
fi
echo -e "${GREEN}Python $PYTHON_VERSION detected${NC}"

# Check Go
echo "Checking Go..."
if ! command -v go &> /dev/null; then
    echo -e "${YELLOW}Go not found. Install from https://go.dev/dl/${NC}"
else
    echo -e "${GREEN}Go detected${NC}"
fi

# Create venv
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install pre-commit
echo "Installing pre-commit hooks..."
pre-commit install
pre-commit autoupdate

# Create .env
echo "Setting up environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${YELLOW}.env created. EDIT IT with your API keys.${NC}"
else
    echo -e "${GREEN}.env already exists${NC}"
fi

# Clone Lobster Trap
if [ ! -d "lobster-trap" ]; then
    echo "Setting up Lobster Trap..."
    git clone https://github.com/veeainc/lobstertrap.git lobster-trap
    cd lobster-trap && make build && cd ..
    echo -e "${GREEN}Lobster Trap compiled${NC}"
fi

# Security check
echo "Running security checks..."
if git check-ignore -q .env 2>/dev/null; then
    echo -e "${GREEN}.env is properly gitignored${NC}"
else
    echo -e "${RED}WARNING: .env is NOT gitignored!${NC}"
fi

echo ""
echo "============================================================"
echo -e "${GREEN}VALLUM Setup Complete!${NC}"
echo "============================================================"
echo ""
echo "Next steps:"
echo "  1. Edit .env with your Gemini API key"
echo "  2. Start Lobster Trap: cd lobster-trap && ./lobstertrap serve"
echo "  3. Run tests: pytest"
echo "  4. Start API: python -m vallum.api"
echo "  5. Start Dashboard: streamlit run vallum/dashboard/app.py"
echo ""
echo -e "${YELLOW}REMEMBER: NEVER commit .env or API keys!${NC}"
echo ""
