#!/bin/bash

# Install Python if not present
if ! command -v python3 &> /dev/null; then
    echo "Python3 not found. Installing..."
    # For Ubuntu/Debian
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip
    # For macOS
    elif command -v brew &> /dev/null; then
        brew install python3
    else
        echo "Please install Python3 manually."
        exit 1
    fi
fi

# Install dependencies
pip3 install -r requirements.txt

# Set environment variables
export PAYMENT_TOKEN="tok_production_998877"
export MAIL_SERVER_KEY="mail_srv_key_ABCDEFG"
export INTERNAL_AUTH="admin_internal_5566"

echo "Setup complete."