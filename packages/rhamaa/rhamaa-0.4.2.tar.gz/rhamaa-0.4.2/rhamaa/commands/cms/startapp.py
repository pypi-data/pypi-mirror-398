import click
import subprocess
import json
import pkgutil
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich import box
from rhamaa.utils import download_github_repo, extract_repo_to_apps, check_wagtail_project

console = Console()

def load_app_registry():
    """Load app registry from JSON file."""
    try:
        data = pkgutil.get_data('rhamaa.templates.cms', 'app_list.json')
        if data is None:
            console.print("[red]Error:[/red] App registry file not found")
            return {}
        return json.loads(data.decode('utf-8'))
    except (json.JSONDecodeError, Exception) as e:
        console.print(f"[red]Error loading app registry:[/red] {e}")
        return {}

def get_app_info(app_name):
    """Get information about a specific app."""
    registry = load_app_registry()
    return registry.get(app_name.lower())

def is_app_available(app_name):
    """Check if an app is available in the registry."""
    registry = load_app_registry()
    return app_name.lower() in registry

@click.command()
@click.argument('app_name', required=False)
@click.option('--type', 'app_type', type=click.Choice(['minimal', 'wagtail']), default='minimal', show_default=True, help='App template type')
@click.option('--prebuild', type=str, default=None, help='Install a prebuilt app from registry (mqtt, users, articles)')
@click.option('--list', 'list_apps', is_flag=True, help='List available prebuilt apps')
@click.option('--force', '-f', is_flag=True, help='Overwrite existing app')
def startapp(app_name, app_type, prebuild, list_apps, force):
    """Create a new Django app or install prebuilt app."""
    
    # Show available apps
    if list_apps:
        show_available_apps()
        return
    
    if not app_name:
        console.print("[red]Error:[/red] Please provide an app name")
        return
    
    # Validate app name
    if not app_name.isidentifier():
        console.print(f"[red]Error:[/red] '{app_name}' is not a valid Python identifier")
        return
    
    # Handle prebuilt app installation
    if prebuild:
        install_prebuilt_app(app_name, prebuild, force)
        return
    
    # Create standard Django app
    create_standard_app(app_name, app_type, force)

def show_available_apps():
    """Display available prebuilt apps."""
    registry = load_app_registry()
    
    if not registry:
        console.print("[red]No prebuilt apps available[/red]")
        return
    
    console.print(Panel(
        "[bold cyan]Available Prebuilt Apps[/bold cyan]\n"
        "[dim]Use: rhamaa cms startapp <app_name> --prebuild <key>[/dim]",
        expand=False
    ))
    
    # Group by category
    categories = {}
    for key, info in registry.items():
        category = info.get('category', 'Other')
        if category not in categories:
            categories[category] = []
        categories[category].append((key, info))
    
    # Display by category
    for category, apps in categories.items():
        console.print(f"\n[bold green]{category}[/bold green]")
        
        table = Table(show_header=True, header_style="bold blue", box=box.SIMPLE)
        table.add_column("Key", style="bold cyan", width=12)
        table.add_column("Name", style="white", width=20)
        table.add_column("Description", style="dim", min_width=30)
        
        for key, info in apps:
            table.add_row(key, info['name'], info['description'])
        
        console.print(table)
    
    console.print(f"\n[dim]Total: {len(registry)} apps available[/dim]")

def install_prebuilt_app(app_name, prebuild_key, force):
    """Install a prebuilt app from registry."""
    if not is_app_available(prebuild_key):
        console.print(f"[red]Error:[/red] Prebuilt app '{prebuild_key}' not found")
        console.print("Use [cyan]rhamaa cms startapp --list[/cyan] to see available apps")
        return
    
    app_dir = Path("apps") / app_name
    if app_dir.exists() and not force:
        console.print(f"[yellow]Warning:[/yellow] App '{app_name}' already exists. Use --force to overwrite")
        return
    
    app_info = get_app_info(prebuild_key)
    console.print(f"[cyan]Installing {app_info['name']} as '{app_name}'...[/cyan]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        
        download_task = progress.add_task("Downloading...", total=100)
        zip_path = download_github_repo(
            app_info['repository'], 
            app_info['branch'], 
            progress, 
            download_task
        )
        
        if not zip_path:
            console.print("[red]Failed to download repository[/red]")
            return
        
        extract_task = progress.add_task("Extracting...", total=100)
        success = extract_repo_to_apps(zip_path, app_name, progress, extract_task)
        
        if success:
            console.print(f"[green]✓[/green] Successfully installed 'apps/{app_name}'")
            console.print(f"[dim]Next steps:[/dim]")
            console.print(f"1. Add 'apps.{app_name}' to INSTALLED_APPS")
            console.print(f"2. Run: python manage.py makemigrations && python manage.py migrate")
        else:
            console.print("[red]Failed to install app[/red]")

def create_standard_app(app_name, app_type, force):
    """Create a standard Django app in apps/ directory."""
    # Ensure apps directory exists
    apps_dir = Path("apps")
    apps_dir.mkdir(exist_ok=True)
    
    app_dir = apps_dir / app_name
    
    if app_dir.exists() and not force:
        console.print(f"[yellow]Warning:[/yellow] Directory 'apps/{app_name}' already exists")
        return
    
    if app_type == 'minimal':
        # Create minimal Django app in apps/ directory
        console.print(f"[cyan]Creating minimal Django app: apps/{app_name}[/cyan]")
        try:
            # Create the app directory first
            app_dir.mkdir(parents=True, exist_ok=True)
            
            # Use django-admin to create app in the apps directory
            subprocess.run(['django-admin', 'startapp', app_name, str(app_dir)], check=True)
            console.print(f"[green]✓[/green] Created 'apps/{app_name}' app")
            
            # Update apps.py to use correct app name path
            apps_py_path = app_dir / 'apps.py'
            if apps_py_path.exists():
                content = apps_py_path.read_text()
                # Replace the name to include apps. prefix
                updated_content = content.replace(
                    f"name = '{app_name}'",
                    f"name = 'apps.{app_name}'"
                )
                apps_py_path.write_text(updated_content)
                
        except subprocess.CalledProcessError:
            console.print("[red]Error:[/red] Failed to create app. Make sure Django is installed")
        except FileNotFoundError:
            console.print("[red]Error:[/red] django-admin not found. Make sure Django is installed")
    else:
        # Create Wagtail-style app with templates
        console.print(f"[cyan]Creating Wagtail app: apps/{app_name}[/cyan]")
        create_app_structure(app_dir, app_name, app_type)
        console.print(f"[green]✓[/green] Created 'apps/{app_name}' app with Wagtail structure")

# Template functions (copied from original startapp.py)
def _render_template(content: str, context: dict) -> str:
    """Very small placeholder renderer using {{var}} tokens."""
    rendered = content
    for key, value in context.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", str(value))
    return rendered

def _read_template(rel_path: str) -> str:
    """Read template file from rhamaa/templates/cms/APPS_TEMPLATES using pkgutil for broad Py support."""
    pkg = 'rhamaa.templates.cms.APPS_TEMPLATES'
    data = pkgutil.get_data(pkg, rel_path)
    if data is None:
        raise FileNotFoundError(f"Template not found: {rel_path}")
    return data.decode('utf-8')

def _write_from_template(rel_template_path: str, dest_path: Path, context: dict):
    content = _read_template(rel_template_path)
    rendered = _render_template(content, context)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.write_text(rendered, encoding='utf-8')

def create_app_structure(app_dir, app_name, app_type='wagtail'):
    """Create Wagtail app structure with templates."""
    
    # Create main directory
    app_dir.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories
    subdirs = ['migrations', 'templates', 'static', 'management', 'management/commands']
    for subdir in subdirs:
        (app_dir / subdir).mkdir(parents=True, exist_ok=True)
    
    # Create templates subdirectory for the app
    (app_dir / 'templates' / app_name).mkdir(parents=True, exist_ok=True)
    
    # Create __init__.py files
    init_files = ['', 'migrations', 'management', 'management/commands']
    for init_path in init_files:
        init_file = app_dir / init_path / '__init__.py' if init_path else app_dir / '__init__.py'
        init_file.touch()
    
    # Context for templates
    context = {
        'app_name': app_name,
        'app_title': app_name.replace('_', ' ').title(),
        'app_verbose_name': app_name.replace('_', ' ').title(),
        'app_config_class': f"{app_name.title().replace('_', '')}Config",
        'app_name_upper': app_name.upper(),
        'app_class_name': app_name.title().replace('_', ''),
    }
    
    # Create app files with Wagtail templates
    prefix = 'wagtail/'
    create_apps_py(app_dir, app_name, context, prefix)
    create_models_py(app_dir, app_name, context, prefix)
    create_views_py(app_dir, app_name, context, prefix)
    create_admin_py(app_dir, app_name, context, prefix)
    create_urls_py(app_dir, app_name, context, prefix)
    create_settings_py(app_dir, app_name, context, prefix)
    create_tests_py(app_dir, app_name, context, prefix)
    create_initial_migration(app_dir, context, prefix)
    create_template_files(app_dir, app_name, context, prefix)

def create_apps_py(app_dir, app_name, context, prefix=''):
    """Create apps.py with RhamaaCMS configuration from template."""
    _write_from_template(f'{prefix}apps.py.tpl', app_dir / 'apps.py', context)

def create_models_py(app_dir, app_name, context, prefix=''):
    """Create models.py from template."""
    _write_from_template(f'{prefix}models.py.tpl', app_dir / 'models.py', context)

def create_views_py(app_dir, app_name, context, prefix=''):
    """Create views.py from template."""
    _write_from_template(f'{prefix}views.py.tpl', app_dir / 'views.py', context)

def create_admin_py(app_dir, app_name, context, prefix=''):
    """Create admin.py from template."""
    _write_from_template(f'{prefix}admin.py.tpl', app_dir / 'admin.py', context)

def create_urls_py(app_dir, app_name, context, prefix=''):
    """Create urls.py for the app from template."""
    _write_from_template(f'{prefix}urls.py.tpl', app_dir / 'urls.py', context)

def create_settings_py(app_dir, app_name, context, prefix=''):
    """Create settings.py from template."""
    _write_from_template(f'{prefix}settings.py.tpl', app_dir / 'settings.py', context)

def create_tests_py(app_dir, app_name, context, prefix=''):
    """Create tests.py from template."""
    _write_from_template(f'{prefix}tests.py.tpl', app_dir / 'tests.py', context)

def create_initial_migration(app_dir, context, prefix=''):
    """Create initial migration file from template."""
    try:
        _write_from_template(f'{prefix}migrations/0001_initial.py.tpl', app_dir / 'migrations' / '0001_initial.py', context)
    except FileNotFoundError:
        pass

def create_template_files(app_dir, app_name, context, prefix=''):
    """Create template files for the app from .tpl files."""
    if prefix == 'wagtail/':
        _write_from_template('wagtail/templates/index.html.tpl', app_dir / 'templates' / app_name / 'index.html', context)
        _write_from_template('wagtail/templates/example_page.html.tpl', app_dir / 'templates' / app_name / 'example_page.html', context)