#!/bin/bash

# Upload to Test PyPI
set -e

echo "🚀 Uploading RhamaaCLI to Test PyPI..."

# Check if dist directory exists
if [ ! -d "dist" ]; then
    echo "❌ No dist directory found. Run build.sh first."
    exit 1
fi

# Upload to Test PyPI
echo "📤 Uploading to Test PyPI..."
python -m twine upload --repository testpypi dist/*

echo "✅ Upload to Test PyPI completed!"
echo ""
echo "To test the installation:"
echo "  pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ rhamaa==0.1.0b1"