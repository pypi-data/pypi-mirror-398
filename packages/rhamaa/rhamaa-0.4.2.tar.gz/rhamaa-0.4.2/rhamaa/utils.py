"""
Utility functions for RhamaaCLI
"""

import os
import shutil
import tempfile
import zipfile
from pathlib import Path
import requests
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

console = Console()


def download_github_repo(repo_url, branch="main", progress=None, task_id=None):
    """
    Download a GitHub repository as a ZIP file.

    Args:
        repo_url (str): GitHub repository URL
        branch (str): Branch to download (default: main)
        progress: Rich progress instance
        task_id: Progress task ID

    Returns:
        str: Path to downloaded ZIP file
    """
    # Convert GitHub URL to ZIP download URL
    if repo_url.endswith('.git'):
        repo_url = repo_url[:-4]

    zip_url = f"{repo_url}/archive/refs/heads/{branch}.zip"

    try:
        if progress and task_id:
            progress.update(
                task_id, description="[cyan]Downloading repository...")

        response = requests.get(zip_url, stream=True)
        response.raise_for_status()

        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')

        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0

        with temp_file as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress and task_id and total_size > 0:
                        progress.update(
                            task_id, completed=downloaded, total=total_size)

        return temp_file.name

    except requests.RequestException as e:
        console.print(f"[red]Error downloading repository: {e}[/red]")
        return None


def extract_repo_to_apps(zip_path, app_name, progress=None, task_id=None):
    """
    Extract downloaded repository to apps/ directory.

    Args:
        zip_path (str): Path to ZIP file
        app_name (str): Name of the app
        progress: Rich progress instance
        task_id: Progress task ID

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if progress and task_id:
            progress.update(task_id, description="[cyan]Extracting files...")

        # Create apps directory if it doesn't exist
        apps_dir = Path("apps")
        apps_dir.mkdir(exist_ok=True)

        app_dir = apps_dir / app_name

        # Remove existing app directory if it exists
        if app_dir.exists():
            shutil.rmtree(app_dir)

        # Extract ZIP file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Get the root directory name from the ZIP
            zip_contents = zip_ref.namelist()
            root_dir = zip_contents[0].split('/')[0] if zip_contents else None

            # Extract to temporary directory first
            temp_extract_dir = tempfile.mkdtemp()
            zip_ref.extractall(temp_extract_dir)

            # Move the extracted content to the correct location
            if root_dir:
                extracted_path = Path(temp_extract_dir) / root_dir
                if extracted_path.exists():
                    shutil.move(str(extracted_path), str(app_dir))
                else:
                    # Fallback: move entire temp directory
                    shutil.move(temp_extract_dir, str(app_dir))
            else:
                shutil.move(temp_extract_dir, str(app_dir))

        if progress and task_id:
            progress.update(task_id, description="[green]Extraction complete!")

        return True

    except Exception as e:
        console.print(f"[red]Error extracting repository: {e}[/red]")
        return False
    finally:
        # Clean up temporary files
        if os.path.exists(zip_path):
            os.unlink(zip_path)


def check_wagtail_project():
    """
    Check if current directory is a Wagtail project.

    Returns:
        bool: True if it's a Wagtail project, False otherwise
    """
    # Check if manage.py exists (primary indicator of Django project)
    manage_py = Path("manage.py")
    if manage_py.exists():
        return True

    # Check for settings directory or file
    if Path("settings.py").exists() or Path("settings").is_dir():
        return True

    # Check for common Django/Wagtail project structure
    common_files = ["requirements.txt", "setup.py", "pyproject.toml"]
    if any(Path(f).exists() for f in common_files):
        return True

    return False
