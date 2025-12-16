#!/usr/bin/env bash
set -e

# Install Python dependencies
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Ensure tests are runnable
pytest -q || true
