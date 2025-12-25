# Contributing

We welcome contributions to Rhamaa CLI! Whether you're fixing bugs, adding features, or creating new apps for the registry, your contributions help make Wagtail development faster and more enjoyable for everyone.

## Ways to Contribute

### 🐛 Bug Reports
Report issues and bugs you encounter while using Rhamaa CLI.

### 💡 Feature Requests
Suggest new features or improvements to existing functionality.

### 🔧 Code Contributions
Submit pull requests with bug fixes, features, or improvements.

### 📦 App Development
Create new prebuilt applications for the registry.

### 📚 Documentation
Improve documentation, tutorials, and examples.

---

## Getting Started

### Development Setup

1. **Fork the Repository**
   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/YOUR_USERNAME/RhamaaCLI.git
   cd RhamaaCLI
   ```

2. **Set Up Development Environment**
   ```bash
   # Create virtual environment
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # .venv\Scripts\activate   # Windows
   
   # Install in development mode
   pip install -e .
   
   # Install development dependencies
   pip install -e ".[dev]"
   ```

3. **Verify Installation**
   ```bash
   rhamaa --help
   ```

### Development Dependencies

The development setup includes:

- **pytest**: Testing framework
- **pytest-cov**: Code coverage
- **black**: Code formatting
- **flake8**: Code linting
- **twine**: Package publishing
- **build**: Package building

## Code Contributions

### Workflow

1. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-description
   ```

2. **Make Changes**
   - Follow the coding standards
   - Add tests for new functionality
   - Update documentation as needed

3. **Test Your Changes**
   ```bash
   # Run tests
   pytest
   
   # Check code coverage
   pytest --cov=rhamaa
   
   # Format code
   black rhamaa/
   
   # Lint code
   flake8 rhamaa/
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   # or
   git commit -m "fix: resolve issue description"
   ```

5. **Push and Create PR**
   ```bash
   git push origin your-branch-name
   # Create pull request on GitHub
   ```

### Coding Standards

#### Code Style

- **PEP 8**: Follow Python style guidelines
- **Black**: Use Black for code formatting
- **Line Length**: Maximum 88 characters
- **Imports**: Use absolute imports, group by standard/third-party/local

#### Naming Conventions

- **Functions**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_CASE`
- **Files**: `snake_case.py`

#### Documentation

- **Docstrings**: Use Google-style docstrings
- **Comments**: Explain complex logic
- **Type Hints**: Use type hints where appropriate

#### Example Code

```python
from typing import Optional
from rich.console import Console

console = Console()

def download_app(app_name: str, force: bool = False) -> Optional[str]:
    """Download an app from the registry.
    
    Args:
        app_name: Name of the app to download
        force: Whether to force download if app exists
        
    Returns:
        Path to downloaded app or None if failed
        
    Raises:
        AppNotFoundError: If app doesn't exist in registry
    """
    if not is_app_available(app_name):
        console.print(f"[red]App '{app_name}' not found[/red]")
        return None
    
    # Implementation here
    return app_path
```

### Testing

#### Writing Tests

- **Test Coverage**: Aim for >90% code coverage
- **Test Types**: Unit tests, integration tests, CLI tests
- **Test Data**: Use fixtures for test data
- **Mocking**: Mock external dependencies

#### Test Structure

```python
import pytest
from unittest.mock import patch, MagicMock
from rhamaa.commands.add import add_app

class TestAddCommand:
    """Test the add command functionality."""
    
    def test_add_app_success(self):
        """Test successful app installation."""
        # Test implementation
        pass
    
    def test_add_app_not_found(self):
        """Test app not found error."""
        # Test implementation
        pass
    
    @patch('rhamaa.utils.download_github_repo')
    def test_add_app_download_failure(self, mock_download):
        """Test download failure handling."""
        mock_download.return_value = None
        # Test implementation
        pass
```

#### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_commands.py

# Run with coverage
pytest --cov=rhamaa --cov-report=html

# Run specific test
pytest tests/test_commands.py::TestAddCommand::test_add_app_success
```

## App Development

### Creating Registry Apps

Apps in the Rhamaa registry must follow specific standards:

#### App Structure

```
your_app/
├── __init__.py
├── models.py
├── views.py
├── admin.py
├── urls.py
├── apps.py
├── migrations/
│   └── __init__.py
├── templates/
│   └── your_app/
├── static/
│   └── your_app/
├── README.md
├── requirements.txt
└── setup.py (optional)
```

#### App Requirements

1. **Django App**: Standard Django app structure
2. **Wagtail Compatible**: Works with current Wagtail versions
3. **Documentation**: Comprehensive README with setup instructions
4. **Dependencies**: Minimal external dependencies
5. **License**: Compatible open-source license

#### README Template

```markdown
# Your App Name

Brief description of your app's functionality.

## Features

- Feature 1
- Feature 2
- Feature 3

## Installation

This app is installed via Rhamaa CLI:

```bash
rhamaa add your_app
```

## Configuration

Add to your Django settings:

```python
INSTALLED_APPS = [
    # ... other apps
    'apps.your_app',
]

# App-specific settings
YOUR_APP_SETTING = 'value'
```

## Usage

Instructions for using the app...

## Requirements

- Django >= 3.2
- Wagtail >= 4.0
- Other dependencies...

## License

Your license information...
```

#### Adding to Registry

To add your app to the registry:

1. **Create App Repository**: Host on GitHub
2. **Follow Standards**: Ensure app meets requirements
3. **Submit PR**: Add app to `rhamaa/registry.py`

```python
# rhamaa/registry.py
APP_REGISTRY = {
    # ... existing apps
    "your_app": {
        "name": "Your App Display Name",
        "description": "Brief description of functionality",
        "repository": "https://github.com/RhamaaCMS/your-app",
        "branch": "main",
        "category": "Appropriate Category"
    }
}
```

### App Categories

Choose the appropriate category:

- **IoT**: Internet of Things, sensors, real-time data
- **Authentication**: User management, permissions, profiles
- **Content**: Publishing, blogs, media management
- **Education**: Learning, courses, assessments
- **E-commerce**: Shopping, payments, inventory
- **Analytics**: Reporting, statistics, monitoring
- **Utilities**: Tools, helpers, integrations

## Documentation Contributions

### Documentation Structure

```
docs/
├── mkdocs.yml
├── docs/
│   ├── index.md
│   ├── getting-started/
│   ├── commands/
│   ├── apps/
│   ├── development/
│   └── help/
```

### Writing Guidelines

- **Clear Language**: Use simple, clear language
- **Code Examples**: Include working code examples
- **Screenshots**: Add screenshots where helpful
- **Cross-references**: Link to related sections

### Building Documentation

```bash
# Install MkDocs
pip install mkdocs-material

# Serve locally
cd docs
mkdocs serve

# Build static site
mkdocs build
```

## Release Process

### Version Management

- **Semantic Versioning**: Use semver (major.minor.patch)
- **Beta Releases**: Use beta versions for testing
- **Changelog**: Maintain detailed changelog

### Release Steps

1. **Update Version**: Update version in `setup.py` and `pyproject.toml`
2. **Update Changelog**: Document changes
3. **Create Tag**: Create git tag for release
4. **Build Package**: Build distribution packages
5. **Upload to PyPI**: Upload to PyPI

```bash
# Build package
python -m build

# Upload to test PyPI
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*
```

## Community Guidelines

### Code of Conduct

- **Be Respectful**: Treat all contributors with respect
- **Be Inclusive**: Welcome contributors from all backgrounds
- **Be Constructive**: Provide helpful feedback
- **Be Patient**: Help newcomers learn

### Communication

- **GitHub Issues**: For bug reports and feature requests
- **Pull Requests**: For code contributions
- **Discussions**: For general questions and ideas

### Recognition

Contributors are recognized in:

- **Changelog**: Major contributions noted
- **README**: Contributors section
- **GitHub**: Contributor statistics

## Getting Help

### Development Questions

- **GitHub Discussions**: Ask questions about development
- **Issues**: Report bugs or request features
- **Code Review**: Get feedback on pull requests

### Resources

- **Django Documentation**: https://docs.djangoproject.com/
- **Wagtail Documentation**: https://docs.wagtail.org/
- **Click Documentation**: https://click.palletsprojects.com/
- **Rich Documentation**: https://rich.readthedocs.io/

## Next Steps

1. **Set Up Development Environment**: Follow the setup guide
2. **Pick an Issue**: Look for "good first issue" labels
3. **Make Your First Contribution**: Start with documentation or small fixes
4. **Join the Community**: Participate in discussions and reviews

Thank you for contributing to Rhamaa CLI! Your contributions help make Wagtail development better for everyone.