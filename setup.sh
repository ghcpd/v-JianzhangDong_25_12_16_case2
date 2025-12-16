#!/usr/bin/env bash
set -euo pipefail
python -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
mkdir -p configs exports logs
echo "Setup complete. Activate the venv with: source .venv/bin/activate"