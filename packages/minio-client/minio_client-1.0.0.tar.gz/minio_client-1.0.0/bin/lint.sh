#!/bin/bash
# Clean all the code.

# https://mypy.readthedocs.io/en/latest/
# https://docs.astral.sh/ruff/

set -e

SOURCES="minio_client"

GREEN='\033[0;32m'
NC='\033[0m'

echo "mypy:" && \
mypy --pretty $SOURCES && \
echo "ruff check py310:" && \
ruff check $SOURCES --target-version=py310 && \
echo "ruff check py314:" && \
ruff check $SOURCES --target-version=py314 && \
echo "ruff format py310:" && \
ruff format --check $SOURCES --target-version=py310 && \
echo "ruff format py314:" && \
ruff format --check $SOURCES --target-version=py314 && \
printf "${GREEN}This code is clean.${NC}\n"
