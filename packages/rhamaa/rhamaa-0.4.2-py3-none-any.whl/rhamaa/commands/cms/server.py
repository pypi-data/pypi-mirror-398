import click
import subprocess
from rich.console import Console
from .utils import run_manage

console = Console()

@click.command()
@click.option('--host', default='127.0.0.1', help='Host to bind to')
@click.option('--port', default='8000', help='Port to bind to')
@click.option('--prod', is_flag=True, help='Run with Gunicorn for production')
def run(host, port, prod):
    """Start development or production server."""
    if prod:
        console.print("[cyan]Starting production server with Gunicorn...[/cyan]")
        try:
            subprocess.run([
                'gunicorn', 
                '--bind', f'{host}:{port}',
                '--workers', '3',
                'config.wsgi:application'
            ], check=True)
        except FileNotFoundError:
            console.print("[red]Error:[/red] Gunicorn not installed. Install with: pip install gunicorn")
        except subprocess.CalledProcessError:
            console.print("[red]Error:[/red] Failed to start Gunicorn server")
    else:
        console.print(f"[cyan]Starting development server on {host}:{port}...[/cyan]")
        run_manage(['runserver', f'{host}:{port}'])