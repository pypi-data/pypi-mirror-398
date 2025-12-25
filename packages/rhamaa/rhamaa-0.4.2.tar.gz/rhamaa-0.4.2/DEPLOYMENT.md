# Deployment Guide for RhamaaCLI

This guide covers how to deploy RhamaaCLI to PyPI.

## Prerequisites

1. **PyPI Account**: Create accounts on both [PyPI](https://pypi.org) and [Test PyPI](https://test.pypi.org)
2. **API Tokens**: Generate API tokens for both accounts
3. **Dependencies**: Install required tools

```bash
pip install build twine
```

## Setup

### 1. Configure PyPI Credentials

Copy the template and fill in your credentials:
```bash
cp .pypirc.template ~/.pypirc
# Edit ~/.pypirc with your API tokens
```

### 2. Make Scripts Executable

```bash
chmod +x scripts/*.sh
```

## Deployment Process

### Step 1: Pre-release Checks

Run comprehensive checks before building:
```bash
./scripts/pre-release-check.sh
```

### Step 2: Build Package

Build the distribution packages:
```bash
./scripts/build.sh
```

This will create:
- `dist/rhamaa-0.1.0b1.tar.gz` (source distribution)
- `dist/rhamaa-0.1.0b1-py3-none-any.whl` (wheel distribution)

### Step 3: Test on Test PyPI

Upload to Test PyPI first:
```bash
./scripts/upload-test.sh
```

Test the installation:
```bash
# Create a test environment
python -m venv test_env
source test_env/bin/activate

# Install from Test PyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ rhamaa==0.1.0b1

# Test the CLI
rhamaa --help
rhamaa startapp test_app

# Clean up
deactivate
rm -rf test_env
```

### Step 4: Deploy to Production PyPI

If testing is successful, deploy to production:
```bash
./scripts/upload-prod.sh
```

## Version Management

### Beta Versions
- Use format: `0.1.0b1`, `0.1.0b2`, etc.
- Update in both `setup.py` and `pyproject.toml`

### Release Candidates
- Use format: `0.1.0rc1`, `0.1.0rc2`, etc.

### Stable Releases
- Use format: `0.1.0`, `0.2.0`, etc.

## Manual Commands

If you prefer manual control:

### Build
```bash
# Clean previous builds
rm -rf build/ dist/ *.egg-info/

# Build
python -m build

# Check
python -m twine check dist/*
```

### Upload
```bash
# Test PyPI
python -m twine upload --repository testpypi dist/*

# Production PyPI
python -m twine upload dist/*
```

## Troubleshooting

### Common Issues

1. **Version already exists**: Increment version number
2. **Authentication failed**: Check API tokens in `~/.pypirc`
3. **Package validation failed**: Run `twine check dist/*`
4. **Missing dependencies**: Install with `pip install build twine`

### Verification

After deployment, verify the package:
```bash
# Check on PyPI
curl -s https://pypi.org/pypi/rhamaa/json | jq '.info.version'

# Test installation
pip install rhamaa==0.1.0b1
rhamaa --help
```

## Security Notes

- Never commit `.pypirc` to version control
- Use API tokens instead of passwords
- Test on Test PyPI before production
- Keep API tokens secure and rotate regularly

## Next Steps

After successful deployment:
1. Update documentation with installation instructions
2. Create GitHub release with changelog
3. Announce on relevant channels
4. Monitor for issues and feedback