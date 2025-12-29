#!/bin/bash
set -e  # Exit on error

# Run database migrations
echo "Running database migrations..."
uv run migrate.py

# Run main application
echo "Starting main application..."
uv run main.py