#!/bin/bash
# Run tests across all supported Python versions.

set -e

VERSIONS=(
    "3.10"
    "3.11"
    "3.12"
    "3.13"
    "3.14"
)

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

for v in "${VERSIONS[@]}"; do
    echo -e "Testing with Python ${v}..."
    if uv run --python "$v" pytest; then
        echo -e "${GREEN}Python ${v} passed.${NC}"
    else
        echo -e "${RED}Python ${v} failed.${NC}"
        exit 1
    fi
    echo "----------------------------------------"
done

echo -e "${GREEN}All versions passed!${NC}"
