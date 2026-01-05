#!/bin/bash

# Setup script for Linux/macOS
set -e

echo "Setting up secure Flask application environment..."

# Check Python version
PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "Python version: $PYTHON_VERSION"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
mkdir -p configs logs

# Create .env file template if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env template..."
    cat > .env.template << 'EOF'
# Required environment variables
PAYMENT_TOKEN=your_payment_token_here
MAIL_SERVER_KEY=your_mail_server_key_here
INTERNAL_AUTH=your_internal_auth_here
FLASK_ENV=development
EOF
    echo "Created .env.template - please configure with your values and rename to .env"
fi

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Configure environment variables in .env file"
echo "2. Run: source venv/bin/activate"
echo "3. Run: python run_test.sh to test the application"
