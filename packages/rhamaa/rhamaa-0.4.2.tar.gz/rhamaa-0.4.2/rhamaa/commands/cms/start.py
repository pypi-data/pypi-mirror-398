import click
import subprocess
import json
import pkgutil
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()

TEMPLATE_REGISTRY_PKG = "rhamaa.templates.cms"  # Package containing template registry
TEMPLATE_REGISTRY_FILE = "project_template_list.json"
DEFAULT_TEMPLATE_KEY = "base"
CLI_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_LOCAL_TEMPLATE = (CLI_ROOT.parent / "RhamaaCMS").resolve()


def load_template_registry():
    """Load available project templates from JSON."""
    try:
        data = pkgutil.get_data(TEMPLATE_REGISTRY_PKG, TEMPLATE_REGISTRY_FILE)
        if data is None:
            console.print("[red]Error:[/red] Project template registry not found")
            return {}
        return json.loads(data.decode("utf-8"))
    except (json.JSONDecodeError, Exception) as exc:
        console.print(f"[red]Error loading project template registry:[/red] {exc}")
        return {}


def get_template_info(template_key):
    registry = load_template_registry()
    return registry.get(template_key.lower()), registry


def show_available_templates():
    registry = load_template_registry()
    if not registry:
        console.print("[red]No project templates available[/red]")
        return

    console.print(
        Panel(
            "[bold cyan]Available RhamaaCMS Templates[/bold cyan]\n"
            "[dim]Use: rhamaa cms start <project_name> --template <key>[/dim]",
            expand=False,
        )
    )

    table = Table(show_header=True, header_style="bold blue", box=box.SIMPLE)
    table.add_column("Key", style="bold cyan", width=12)
    table.add_column("Name", style="white", width=24)
    table.add_column("Branch", style="white", width=10)
    table.add_column("Description", style="dim", min_width=32)

    for key, info in registry.items():
        table.add_row(
            key,
            info.get("name", "-"),
            info.get("branch", "-"),
            info.get("description", "-"),
        )

    console.print(table)
    console.print(f"[dim]Total: {len(registry)} templates[/dim]")


def build_github_zip_url(repo_url: str, branch: str) -> str:
    if repo_url.endswith(".git"):
        repo_url = repo_url[:-4]
    return f"{repo_url}/archive/refs/heads/{branch}.zip"


@click.command()
@click.argument("project_name", required=False)
@click.option(
    "--template",
    "template_key",
    default=DEFAULT_TEMPLATE_KEY,
    show_default=True,
    help="Template key defined in project_template_list.json (e.g. base, dev).",
)
@click.option(
    "--template-url",
    type=str,
    help="Custom template ZIP URL (overrides --template registry selection).",
)
@click.option(
    "--template-file",
    type=click.Path(exists=True, path_type=Path),
    help="Path to local template ZIP or directory (overrides --template registry selection).",
)
@click.option(
    "--local-dev",
    is_flag=True,
    help="Use local RhamaaCMS template from ../RhamaaCMS instead of downloading a branch.",
)
@click.option(
    "--list",
    "list_templates",
    is_flag=True,
    help="List available templates and exit.",
)
def start(project_name, template_key, template_url, template_file, local_dev, list_templates):
    """Create a new Wagtail project using the RhamaaCMS template."""
    if list_templates:
        show_available_templates()
        return

    if not project_name:
        console.print("[red]Error:[/red] Please provide a project name.")
        return

    template_source = None

    if template_file:
        template_path = template_file.expanduser().resolve()
        if not template_path.exists():
            console.print(
                Panel(
                    f"[red]Error:[/red] Template file or directory not found: {template_path}",
                    expand=False,
                )
            )
            return
        template_source = str(template_path)
        console.print(
            Panel(
                f"[green]Using local template file/directory:[/green] {template_path}",
                expand=False,
            )
        )
    elif template_url:
        if not template_url.lower().startswith(("http://", "https://")):
            console.print(
                Panel(
                    "[red]Error:[/red] Template URL must start with http:// or https://",
                    expand=False,
                )
            )
            return
        template_source = template_url
        console.print(
            Panel(
                f"[green]Using custom template URL:[/green]\n[dim]{template_url}[/dim]",
                expand=False,
            )
        )
    elif local_dev:
        template_source = DEFAULT_LOCAL_TEMPLATE
        if not template_source.exists():
            console.print(
                Panel(
                    f"[red]Error:[/red] Local template path not found: {template_source}",
                    expand=False,
                )
            )
            return
        console.print(
            Panel(
                f"[green]Using local RhamaaCMS template:[/green] {template_source}",
                expand=False,
            )
        )
    else:
        template_info, registry = get_template_info(template_key)
        if not template_info:
            available = ", ".join(sorted(registry.keys())) if registry else "none"
            console.print(
                Panel(
                    f"[red]Error:[/red] Template key '{template_key}' not found.\n"
                    f"Available keys: {available}",
                    expand=False,
                )
            )
            return
        repo_url = template_info.get("repository")
        branch = template_info.get("branch", "main")
        template_source = build_github_zip_url(repo_url, branch)
        console.print(
            Panel(
                f"[green]Selected template:[/green] [bold]{template_key}[/bold]\n"
                f"[dim]{template_info.get('description', '')}[/dim]\n"
                f"[dim]{template_source}[/dim]",
                expand=False,
            )
        )

    cmd = [
        "wagtail",
        "start",
        f"--template={template_source}",
        project_name,
    ]
    console.print(
        Panel(
            f"[green]Creating new Wagtail project:[/green] [bold]{project_name}[/bold]",
            expand=False,
        )
    )
    try:
        subprocess.run(cmd, check=True)
        console.print(
            Panel(f"[bold green]Project {project_name} created![/bold green]", expand=False)
        )
    except subprocess.CalledProcessError:
        console.print("[red]Error:[/red] Failed to create project. Make sure Wagtail is installed")
    except FileNotFoundError:
        console.print("[red]Error:[/red] wagtail command not found. Install with: pip install wagtail")