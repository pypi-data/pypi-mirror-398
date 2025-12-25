import click
from rich.console import Console
from .utils import run_manage

console = Console()

@click.command()
def migrate():
    """Run database migrations."""
    console.print("[cyan]Running migrations...[/cyan]")
    run_manage(['migrate'])

@click.command()
@click.argument('app', required=False)
def makemigrations(app):
    """Create new migrations."""
    if app:
        console.print(f"[cyan]Creating migrations for {app}...[/cyan]")
        run_manage(['makemigrations', app])
    else:
        console.print("[cyan]Creating migrations...[/cyan]")
        run_manage(['makemigrations'])