# API Reference

This section provides detailed technical documentation for Rhamaa CLI's internal APIs, modules, and functions. This is primarily useful for contributors and developers extending the CLI.

## Core Modules

### `rhamaa.cli`

Main CLI entry point and command group definition.

#### Functions

##### `main(ctx)`

Main Click command group that serves as the entry point for all CLI commands.

```python
@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    """Rhamaa CLI for Wagtail development."""
```

**Parameters:**
- `ctx` (click.Context): Click context object

**Behavior:**
- Shows logo and help if no subcommand is provided
- Registers all subcommands

##### `show_logo_and_help()`

Displays the ASCII logo and command help table.

```python
def show_logo_and_help():
    """Display ASCII logo and help information."""
```

**Features:**
- Rich-formatted ASCII art logo
- Formatted command table
- Links to documentation

#### Constants

```python
ASCII_LOGO: str  # Multi-line ASCII art string
HELP_COMMANDS: List[Tuple[str, str]]  # Command descriptions
HELP_PANEL_TEXT: str  # Help panel content
```

### `rhamaa.registry`

App registry management and data structures.

#### Constants

##### `APP_REGISTRY`

Main registry dictionary containing all available applications.

```python
APP_REGISTRY: Dict[str, Dict[str, str]] = {
    "app_key": {
        "name": "Display Name",
        "description": "App description",
        "repository": "GitHub repository URL",
        "branch": "Git branch name",
        "category": "App category"
    }
}
```

#### Functions

##### `get_app_info(app_name)`

Retrieve information about a specific app from the registry.

```python
def get_app_info(app_name: str) -> Optional[Dict[str, str]]:
    """Get information about a specific app."""
```

**Parameters:**
- `app_name` (str): Name of the app to look up

**Returns:**
- `Dict[str, str]`: App information dictionary or None if not found

**Example:**
```python
info = get_app_info('mqtt')
if info:
    print(f"App: {info['name']}")
    print(f"Description: {info['description']}")
```

##### `list_available_apps()`

Get the complete list of available applications.

```python
def list_available_apps() -> Dict[str, Dict[str, str]]:
    """Get list of all available apps."""
```

**Returns:**
- `Dict[str, Dict[str, str]]`: Complete registry dictionary

##### `is_app_available(app_name)`

Check if an application exists in the registry.

```python
def is_app_available(app_name: str) -> bool:
    """Check if an app is available in the registry."""
```

**Parameters:**
- `app_name` (str): Name of the app to check

**Returns:**
- `bool`: True if app exists, False otherwise

### `rhamaa.utils`

Utility functions for file operations, downloads, and project validation.

#### Functions

##### `download_github_repo(repo_url, branch, progress, task_id)`

Download a GitHub repository as a ZIP file with progress tracking.

```python
def download_github_repo(
    repo_url: str, 
    branch: str = "main", 
    progress: Optional[Progress] = None, 
    task_id: Optional[int] = None
) -> Optional[str]:
    """Download a GitHub repository as a ZIP file."""
```

**Parameters:**
- `repo_url` (str): GitHub repository URL
- `branch` (str): Git branch to download (default: "main")
- `progress` (Optional[Progress]): Rich progress instance
- `task_id` (Optional[int]): Progress task ID

**Returns:**
- `Optional[str]`: Path to downloaded ZIP file or None if failed

**Raises:**
- `requests.RequestException`: On network or HTTP errors

**Example:**
```python
from rich.progress import Progress

with Progress() as progress:
    task = progress.add_task("Downloading...", total=100)
    zip_path = download_github_repo(
        "https://github.com/RhamaaCMS/mqtt-apps",
        "main",
        progress,
        task
    )
```

##### `extract_repo_to_apps(zip_path, app_name, progress, task_id)`

Extract downloaded repository to the apps directory.

```python
def extract_repo_to_apps(
    zip_path: str, 
    app_name: str, 
    progress: Optional[Progress] = None, 
    task_id: Optional[int] = None
) -> bool:
    """Extract downloaded repository to apps/ directory."""
```

**Parameters:**
- `zip_path` (str): Path to ZIP file
- `app_name` (str): Name of the app directory
- `progress` (Optional[Progress]): Rich progress instance
- `task_id` (Optional[int]): Progress task ID

**Returns:**
- `bool`: True if successful, False otherwise

**Side Effects:**
- Creates `apps/` directory if it doesn't exist
- Removes existing app directory if present
- Cleans up temporary files

##### `check_wagtail_project()`

Validate if the current directory is a Wagtail project.

```python
def check_wagtail_project() -> bool:
    """Check if current directory is a Wagtail project."""
```

**Returns:**
- `bool`: True if valid Wagtail project, False otherwise

**Validation Criteria:**
- Presence of `manage.py` file
- Existence of `settings.py` or `settings/` directory
- Common Django project files

## Command Modules

### `rhamaa.commands.start`

Project creation functionality.

#### Commands

##### `start(project_name)`

Create a new Wagtail project using the RhamaaCMS template.

```python
@click.command()
@click.argument('project_name')
def start(project_name: str):
    """Create a new Wagtail project using the RhamaaCMS template."""
```

**Parameters:**
- `project_name` (str): Name of the project to create

**Behavior:**
- Downloads RhamaaCMS template
- Executes `wagtail start` with template
- Provides user feedback

**Requirements:**
- Wagtail must be installed
- Internet connection for template download

### `rhamaa.commands.add`

Application installation functionality.

#### Commands

##### `add(app_name, list, force)`

Install prebuilt applications from the registry.

```python
@click.command()
@click.argument('app_name', required=False)
@click.option('--list', '-l', is_flag=True, help='List all available apps')
@click.option('--force', '-f', is_flag=True, help='Force install even if app already exists')
def add(app_name: Optional[str], list: bool, force: bool):
    """Add a prebuilt app to the project."""
```

**Parameters:**
- `app_name` (Optional[str]): Name of app to install
- `list` (bool): Show available apps instead of installing
- `force` (bool): Overwrite existing app installation

**Behavior:**
- Validates Wagtail project
- Checks app availability
- Downloads and installs app
- Provides installation instructions

#### Helper Functions

##### `show_available_apps()`

Display formatted table of available applications.

```python
def show_available_apps():
    """Display all available apps in a formatted table."""
```

**Output:**
- Rich-formatted table with app information
- Grouped by categories
- Installation instructions

##### `install_app(app_name, app_info)`

Perform the actual app installation process.

```python
def install_app(app_name: str, app_info: Dict[str, str]):
    """Install an app from the registry."""
```

**Parameters:**
- `app_name` (str): Name of the app
- `app_info` (Dict[str, str]): App information from registry

**Process:**
1. Download repository
2. Extract to apps directory
3. Provide post-installation instructions

### `rhamaa.commands.registry`

Registry management commands.

#### Command Groups

##### `registry()`

Main registry command group.

```python
@click.group()
def registry():
    """Manage app registry."""
```

#### Subcommands

##### `list()`

Display all apps in the registry organized by category.

```python
@registry.command()
def list():
    """List all apps in the registry."""
```

**Output:**
- Apps grouped by category
- Detailed information table
- Total app count

##### `info(app_name)`

Show detailed information about a specific app.

```python
@registry.command()
@click.argument('app_name')
def info(app_name: str):
    """Show detailed information about a specific app."""
```

**Parameters:**
- `app_name` (str): Name of the app to display

**Output:**
- Formatted panel with app details
- Installation command
- Repository information

##### `update()`

Placeholder for future registry update functionality.

```python
@registry.command()
def update():
    """Update the app registry (placeholder for future implementation)."""
```

**Current Behavior:**
- Shows "coming soon" message
- Explains current limitations

## Data Structures

### App Registry Entry

Each app in the registry follows this structure:

```python
AppEntry = TypedDict('AppEntry', {
    'name': str,           # Display name
    'description': str,    # Brief description
    'repository': str,     # GitHub repository URL
    'branch': str,         # Git branch name
    'category': str        # App category
})
```

### Categories

Standard app categories:

```python
CATEGORIES = [
    "IoT",              # Internet of Things
    "Authentication",   # User management
    "Content",         # Content management
    "Education",       # Learning management
    "E-commerce",      # Shopping and payments
    "Analytics",       # Reporting and statistics
    "Utilities"        # Tools and integrations
]
```

## Error Handling

### Custom Exceptions

While Rhamaa CLI doesn't define custom exceptions yet, it handles these standard exceptions:

- `requests.RequestException`: Network and HTTP errors
- `zipfile.BadZipFile`: Corrupted ZIP files
- `FileNotFoundError`: Missing files or directories
- `PermissionError`: File system permission issues
- `click.ClickException`: CLI-specific errors

### Error Messages

Error messages follow this pattern:

```python
console.print(Panel(
    f"[red]Error:[/red] {error_description}\n"
    f"{helpful_suggestion}",
    title="[red]Error Title[/red]",
    expand=False
))
```

## Configuration

### Environment Variables

Currently, Rhamaa CLI doesn't use environment variables, but future versions may support:

```python
RHAMAA_REGISTRY_URL: str     # Custom registry URL
RHAMAA_CACHE_DIR: str        # Cache directory
RHAMAA_TIMEOUT: int          # Download timeout
RHAMAA_DEBUG: bool           # Debug mode
```

### Settings

Future configuration file structure:

```python
# ~/.rhamaa/config.yaml
registry:
  url: "https://registry.rhamaacms.com"
  cache_ttl: 3600
  
download:
  timeout: 30
  retries: 3
  
ui:
  theme: "auto"
  progress: true
```

## Extension Points

### Adding New Commands

To add a new command:

1. Create module in `rhamaa/commands/`
2. Define Click command
3. Register in `cli.py`

```python
# rhamaa/commands/mycommand.py
import click

@click.command()
def mycommand():
    """My custom command."""
    pass

# rhamaa/cli.py
from rhamaa.commands.mycommand import mycommand
main.add_command(mycommand)
```

### Custom App Sources

Future API for custom app sources:

```python
from rhamaa.registry import register_source

register_source("custom", {
    "url": "https://my-registry.com/api",
    "auth": "token",
    "format": "json"
})
```

## Testing APIs

### Test Utilities

For testing CLI commands:

```python
from click.testing import CliRunner
from rhamaa.cli import main

def test_help_command():
    runner = CliRunner()
    result = runner.invoke(main, ['--help'])
    assert result.exit_code == 0
    assert 'Rhamaa CLI' in result.output
```

### Mock Objects

For testing with mocked dependencies:

```python
from unittest.mock import patch, MagicMock

@patch('rhamaa.utils.download_github_repo')
def test_app_installation(mock_download):
    mock_download.return_value = '/tmp/test.zip'
    # Test implementation
```

## Performance Considerations

### Caching

Future caching implementation:

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_app_info_cached(app_name: str) -> Optional[Dict[str, str]]:
    """Cached version of get_app_info."""
    return get_app_info(app_name)
```

### Async Operations

Future async support:

```python
import asyncio
import aiohttp

async def download_github_repo_async(repo_url: str) -> Optional[str]:
    """Async version of repository download."""
    # Implementation
```

## Debugging

### Debug Mode

Enable debug output:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('rhamaa')
```

### Verbose Output

Future verbose mode:

```bash
rhamaa --verbose add mqtt
rhamaa -v registry list
```

This API reference will be updated as Rhamaa CLI evolves. For the most current information, check the source code and inline documentation.