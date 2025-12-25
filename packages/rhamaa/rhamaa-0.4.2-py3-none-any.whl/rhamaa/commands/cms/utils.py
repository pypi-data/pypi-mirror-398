import subprocess
from pathlib import Path
from rich.console import Console

console = Console()

def is_django_project():
    """Check if current directory is a Django project."""
    return Path("manage.py").exists()

def run_manage(args):
    """Run Django management command."""
    try:
        subprocess.run(['python', 'manage.py'] + args, check=True)
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error:[/red] Command failed with exit code {e.returncode}")
    except FileNotFoundError:
        console.print("[red]Error:[/red] Python or manage.py not found")