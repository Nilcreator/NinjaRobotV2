#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting NinjaRobot V2 Setup...${NC}"

# Check for uv
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}uv is not installed. Installing uv...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Add uv to path for this session if needed (though the script usually handles it)
    source $HOME/.cargo/env 2>/dev/null || true
else
    echo -e "${GREEN}uv is already installed.${NC}"
fi

# Create virtual environment and install dependencies
echo -e "${GREEN}Syncing dependencies with uv...${NC}"
uv sync

echo -e "${GREEN}Setup complete!${NC}"
echo -e "Activate the environment with: ${YELLOW}source .venv/bin/activate${NC}"
