#!/bin/bash

# Rhamaa CLI Documentation Server
# This script sets up and serves the documentation locally

set -e

echo "🚀 Starting Rhamaa CLI Documentation Server..."

# Check if we're in the docs directory
if [ ! -f "mkdocs.yml" ]; then
    echo "❌ Error: mkdocs.yml not found. Please run this script from the docs/ directory."
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is required but not installed."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ Error: pip3 is required but not installed."
    exit 1
fi

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "📦 Installing documentation dependencies..."
    pip3 install -r requirements.txt
else
    echo "📦 Installing MkDocs and Material theme..."
    pip3 install mkdocs mkdocs-material mkdocs-static-i18n pymdown-extensions
fi

# Check if MkDocs is installed
if ! command -v mkdocs &> /dev/null; then
    echo "❌ Error: MkDocs installation failed."
    exit 1
fi

echo "✅ Dependencies installed successfully!"

# Start the development server
echo "🌐 Starting MkDocs development server..."
echo "📖 Documentation will be available at: http://127.0.0.1:8000"
echo "🔄 The server will automatically reload when you make changes."
echo "⏹️  Press Ctrl+C to stop the server."
echo ""

mkdocs serve