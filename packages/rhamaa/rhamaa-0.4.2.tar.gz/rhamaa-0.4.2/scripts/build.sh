#!/bin/bash

# Build script for RhamaaCLI
set -e

echo "🔧 Building RhamaaCLI for PyPI..."

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/
rm -rf dist/
rm -rf *.egg-info/

# Install build dependencies
echo "📦 Installing build dependencies..."
pip install --upgrade build twine

# Build the package
echo "🏗️  Building package..."
python -m build

# Check the built package
echo "🔍 Checking built package..."
python -m twine check dist/*

echo "✅ Build completed successfully!"
echo "📁 Built files are in the 'dist/' directory"
echo ""
echo "To upload to PyPI:"
echo "  Test PyPI: python -m twine upload --repository testpypi dist/*"
echo "  Real PyPI: python -m twine upload dist/*"