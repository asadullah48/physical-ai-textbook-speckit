#!/bin/bash
# Physical AI Textbook - Development Environment Setup
# Usage: ./scripts/setup-dev.sh

set -e

echo "=========================================="
echo "Physical AI Textbook - Development Setup"
echo "=========================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo -e "${RED}Error: $1 is not installed${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓${NC} $1 found"
}

echo "Checking prerequisites..."
check_command python3
check_command node
check_command npm

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if [[ $(echo "$PYTHON_VERSION < 3.11" | bc -l) -eq 1 ]]; then
    echo -e "${RED}Error: Python 3.11+ required (found $PYTHON_VERSION)${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION"

# Check Node version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [[ $NODE_VERSION -lt 20 ]]; then
    echo -e "${RED}Error: Node.js 20+ required (found v$NODE_VERSION)${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} Node.js $(node -v)"

echo ""
echo "Setting up Backend..."
echo "---------------------"

cd backend

# Create Python virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
pip install --quiet -r requirements-dev.txt

# Create .env from example if not exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env from .env.example${NC}"
    cp .env.example .env
    echo -e "${YELLOW}⚠ Please update backend/.env with your credentials${NC}"
fi

# Create __init__.py files
touch src/__init__.py
touch src/api/__init__.py
touch src/api/routes/__init__.py
touch src/api/middleware/__init__.py
touch src/models/__init__.py
touch src/services/__init__.py
touch src/db/__init__.py
touch src/scripts/__init__.py

echo -e "${GREEN}✓${NC} Backend setup complete"

cd ..

echo ""
echo "Setting up Frontend..."
echo "----------------------"

cd frontend

# Install npm dependencies
echo "Installing npm dependencies..."
npm install --silent

# Create .env from example if not exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env from .env.example${NC}"
    cp .env.example .env
fi

echo -e "${GREEN}✓${NC} Frontend setup complete"

cd ..

echo ""
echo "=========================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Update backend/.env with your database and API credentials"
echo "  2. Run database migrations: cd backend && alembic upgrade head"
echo "  3. Start backend: cd backend && uvicorn src.api.main:app --reload"
echo "  4. Start frontend: cd frontend && npm run start"
echo ""
echo "For more information, see specs/001-physical-ai-textbook/quickstart.md"
