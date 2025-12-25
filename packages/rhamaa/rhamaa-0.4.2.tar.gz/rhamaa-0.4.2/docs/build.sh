#!/bin/bash

# Rhamaa CLI Documentation Builder
# This script builds the static documentation site

set -e

echo "🏗️  Building Rhamaa CLI Documentation..."

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

# Clean previous build
if [ -d "site" ]; then
    echo "🧹 Cleaning previous build..."
    rm -rf site
fi

# Build the documentation
echo "🔨 Building static documentation site..."
mkdocs build

# Check if build was successful
if [ -d "site" ]; then
    echo "✅ Documentation built successfully!"
    echo "📁 Static files are in the 'site/' directory"
    echo "🌐 You can serve them with any web server"
    echo ""
    echo "💡 To serve locally, run:"
    echo "   cd site && python3 -m http.server 8000"
    echo ""
    echo "🚀 To deploy to GitHub Pages, run:"
    echo "   mkdocs gh-deploy"
else
    echo "❌ Error: Build failed. Check the output above for errors."
    exit 1
fi