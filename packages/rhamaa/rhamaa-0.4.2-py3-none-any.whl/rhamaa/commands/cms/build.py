import json
import shutil
import tempfile
import zipfile
from pathlib import Path
import re

import click
from rich.console import Console
from rich.panel import Panel

console = Console()

IGNORE_PATTERNS = [
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    "*.pyc",
    "node_modules",
    ".ruff_cache",
    ".mypy_cache",
    ".idea",
    ".vscode",
    "dist",
]


@click.command("build-template")
@click.argument("source", required=False, default=".")
@click.option(
    "--slug",
    "slug",
    default=None,
    help="Project slug used when the template project was generated (defaults to folder name).",
)
@click.option(
    "--output",
    "output",
    default="rhamaacms-template.zip",
    help="Filename (relative or absolute) for the generated zip.",
)
@click.option(
    "--wrap-templates/--no-wrap-templates",
    default=True,
    help="Wrap HTML templates with verbatim tags (recommended).",
)
def build_template(source, slug, output, wrap_templates):
    """Convert a generated RhamaaCMS project back into a distributable template."""

    source_path = Path(source).resolve()
    if not source_path.exists():
        console.print(Panel(f"[red]Error:[/red] Source directory not found: {source_path}", expand=False))
        return

    slug = (slug or source_path.name).strip()
    if not slug:
        console.print(Panel("[red]Error:[/red] Could not determine project slug.", expand=False))
        return

    console.print(Panel(f"[green]Preparing template from:[/green] {source_path}", expand=False))

    work_parent = source_path.parent
    with tempfile.TemporaryDirectory(prefix="rhamaa_template_", dir=work_parent) as tmp_dir:
        sandbox_dir = Path(tmp_dir)
        project_copy = sandbox_dir / "project"

        try:
            shutil.copytree(
                source_path,
                project_copy,
                ignore=shutil.ignore_patterns(*IGNORE_PATTERNS),
                dirs_exist_ok=False,
            )
        except Exception as exc:
            console.print(Panel(f"[red]Error copying project:[/red] {exc}", expand=False))
            return

        rename_project_package(project_copy, slug)
        replace_slug_tokens(project_copy, slug)

        if wrap_templates:
            wrap_project_templates(project_copy)

        dist_dir = source_path / "dist"
        dist_dir.mkdir(parents=True, exist_ok=True)
        dist_template = dist_dir / "template"
        if dist_template.exists():
            shutil.rmtree(dist_template)
        shutil.copytree(project_copy, dist_template)

        output_path = Path(output)
        if not output_path.is_absolute():
            output_path = dist_dir / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)

        create_zip(dist_template, output_path)

        console.print(
            Panel(
                f"[bold green]Template ready![/bold green]\n"
                f"Tree: {dist_template}\n"
                f"Zip:  {output_path}",
                expand=False,
            )
        )


def slug_variants(slug: str) -> dict:
    lower = slug.lower()
    snake = lower.replace("-", "_")
    kebab = lower.replace("_", "-")
    upper = slug.upper()
    title = re.sub(r"(?:^|[_-])(\w)", lambda m: m.group(1).upper(), lower)

    variants = {
        slug: "{{ project_name }}",
        lower: "{{ project_name }}",
        snake: "{{ project_name }}",
        kebab: "{{ project_name }}",
        title: "{{ project_name }}",
        upper: "{{ project_name|upper }}",
    }
    return {k: v for k, v in variants.items() if k}


def rename_project_package(project_copy: Path, slug: str) -> None:
    candidates = slug_variants(slug).keys()
    target = project_copy / "project_name"
    for name in candidates:
        candidate_path = project_copy / name
        if candidate_path.exists() and candidate_path.is_dir():
            if target.exists():
                shutil.rmtree(target)
            candidate_path.rename(target)
            console.print(f"→ Renamed package '{name}' → 'project_name'")
            break


def replace_slug_tokens(project_copy: Path, slug: str) -> None:
    replacements = slug_variants(slug)

    for path in project_copy.rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        updated = text
        for needle, replacement in replacements.items():
            updated = updated.replace(needle, replacement)

        if updated != text:
            path.write_text(updated, encoding="utf-8")


def wrap_project_templates(project_copy: Path) -> None:
    for templates_dir in {p for p in project_copy.rglob("templates") if p.is_dir()}:
        for html_file in templates_dir.rglob("*.html"):
            wrap_html_file(html_file)


def wrap_html_file(path: Path) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return

    if "{% verbatim %}" in text:
        return

    wrapped = "{% verbatim %}\n" + text + "\n{% endverbatim %}\n"
    path.write_text(wrapped, encoding="utf-8")


def create_zip(source_dir: Path, zip_path: Path) -> None:
    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for path in source_dir.rglob("*"):
            archive_name = path.relative_to(source_dir)
            if path.is_dir():
                continue
            zipf.write(path, archive_name)
