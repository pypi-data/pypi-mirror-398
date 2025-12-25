import click
from rich.console import Console
from .utils import run_manage

console = Console()

@click.command()
def check():
    """Run Django system checks."""
    console.print("[cyan]Running system checks...[/cyan]")
    run_manage(['check'])

@click.command()
@click.argument('app', required=False)
def test(app):
    """Run tests."""
    if app:
        console.print(f"[cyan]Running tests for {app}...[/cyan]")
        run_manage(['test', app])
    else:
        console.print("[cyan]Running all tests...[/cyan]")
        run_manage(['test'])

@click.command()
def collectstatic():
    """Collect static files."""
    console.print("[cyan]Collecting static files...[/cyan]")
    run_manage(['collectstatic', '--noinput'])

@click.command()
def createsuperuser():
    """Create superuser account."""
    console.print("[cyan]Creating superuser...[/cyan]")
    run_manage(['createsuperuser'])

@click.command()
def shell():
    """Open Django shell."""
    console.print("[cyan]Opening Django shell...[/cyan]")
    run_manage(['shell'])

@click.command()
def update_index():
    """Update Wagtail search index."""
    console.print("[cyan]Updating search index...[/cyan]")
    run_manage(['update_index'])