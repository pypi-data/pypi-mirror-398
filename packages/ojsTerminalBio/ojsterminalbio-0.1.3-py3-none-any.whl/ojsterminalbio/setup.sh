#!/bin/bash
# ojsTerminalBio Setup Script for macOS/Linux

echo "=========================================="
echo "  ojsTerminalBio Setup"
echo "=========================================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.10+"
    exit 1
fi

echo "✓ Python found: $(python3 --version)"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install package
echo ""
echo "Installing ojsTerminalBio..."
pip install --upgrade pip
pip install ojsterminalbio

# Initialize database
echo ""
echo "Initializing database..."
ojsterminalbio init-db

# Done
echo ""
echo "=========================================="
echo "  ✓ Setup Complete!"
echo "=========================================="
echo ""
echo "To start the server:"
echo "  source venv/bin/activate"
echo "  ojsterminalbio runserver"
echo ""
echo "Access: http://localhost:7777"
echo "Login:  admin@example.com / admin123"
echo ""
