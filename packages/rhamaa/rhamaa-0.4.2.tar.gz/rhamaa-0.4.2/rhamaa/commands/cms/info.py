import click
import subprocess
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()

@click.command()
def status():
    """Show project status and information."""
    console.print(Panel(
        "[bold cyan]RhamaaCMS Project Status[/bold cyan]",
        expand=False
    ))
    
    # Project info
    project_path = Path.cwd()
    console.print(f"[dim]Project Path:[/dim] {project_path}")
    
    # Check manage.py
    manage_py = project_path / "manage.py"
    if manage_py.exists():
        console.print("[green]✓[/green] manage.py found")
    else:
        console.print("[red]✗[/red] manage.py not found")
    
    # Check apps directory
    apps_dir = project_path / "apps"
    if apps_dir.exists():
        app_count = len([d for d in apps_dir.iterdir() if d.is_dir() and not d.name.startswith('.')])
        console.print(f"[green]✓[/green] apps/ directory ({app_count} apps)")
    else:
        console.print("[yellow]⚠[/yellow] apps/ directory not found")
    
    # Check requirements
    req_files = ['requirements.txt', 'requirements/base.txt', 'pyproject.toml']
    req_found = False
    for req_file in req_files:
        if (project_path / req_file).exists():
            console.print(f"[green]✓[/green] {req_file} found")
            req_found = True
            break
    
    if not req_found:
        console.print("[yellow]⚠[/yellow] No requirements file found")

@click.command()
def info():
    """Show detailed project information."""
    console.print("[cyan]Gathering project information...[/cyan]")
    
    table = Table(show_header=True, header_style="bold blue", box=box.ROUNDED)
    table.add_column("Component", style="bold white", width=20)
    table.add_column("Status", style="white", width=15)
    table.add_column("Details", style="dim", min_width=30)
    
    # Django version
    try:
        result = subprocess.run(['python', '-c', 'import django; print(django.get_version())'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            table.add_row("Django", "[green]Installed[/green]", f"v{result.stdout.strip()}")
        else:
            table.add_row("Django", "[red]Not Found[/red]", "Not installed")
    except:
        table.add_row("Django", "[red]Error[/red]", "Could not check")
    
    # Wagtail version
    try:
        result = subprocess.run(['python', '-c', 'import wagtail; print(wagtail.__version__)'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            table.add_row("Wagtail", "[green]Installed[/green]", f"v{result.stdout.strip()}")
        else:
            table.add_row("Wagtail", "[red]Not Found[/red]", "Not installed")
    except:
        table.add_row("Wagtail", "[red]Error[/red]", "Could not check")
    
    console.print(table)