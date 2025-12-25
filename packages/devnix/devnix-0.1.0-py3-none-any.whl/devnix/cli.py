"""Main CLI entry point for Devnix."""

import sys

import typer
from rich.console import Console

from devnix import __version__
from devnix.detector import get_project_name
from devnix.runners import run_project
from devnix.doctor import run_doctor
from devnix.checker import run_check
from devnix.cleaner import clean_project
from devnix.envsync import check_env, generate_env_example
from pathlib import Path

app = typer.Typer(
    name="devnix",
    help="Devnix - Safe, opinionated Python project workflows",
    add_completion=False,
)
console = Console()


def version_callback(value: bool):
    """Show version and exit."""
    if value:
        console.print(f"Devnix version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit",
        callback=version_callback,
        is_eager=True,
    )
):
    """Devnix - Safe, opinionated Python project workflows."""
    pass


@app.command()
def run():
    """
    Run the project automatically.
    
    Auto-detects project type (Django, FastAPI, Flask, Script) and runs
    the appropriate command. Loads .env file automatically.
    """
    try:
        run_project()
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped[/yellow]")
        sys.exit(0)


@app.command()
def doctor():
    """
    Check project health and safety.
    
    Runs comprehensive checks:
    - Python version compatibility
    - Virtual environment status
    - .env file and variables
    - Git secrets scanning
    - Dependencies
    - Port availability
    """
    run_doctor()


@app.command()
def check():
    """
    Run tests and linters.
    
    Executes in sequence:
    - pytest (tests)
    - black (formatting)
    - isort (import sorting)
    - flake8 (linting)
    
    Stops on first failure.
    """
    success = run_check()
    if not success:
        sys.exit(1)


@app.command()
def clean():
    """
    Clean Python cache files.
    
    Removes:
    - __pycache__
    - .pytest_cache
    - .mypy_cache
    - .ruff_cache
    - *.pyc files
    
    Asks before removing virtual environments.
    """
    clean_project()


# Environment subcommand group
env_app = typer.Typer(help="Check environment variables.")
app.add_typer(env_app, name="env")


@env_app.command("check")
def env_check():
    """
    Compare .env vs .env.example and detect issues.
    """
    check_env()


@env_app.command("generate")
def env_generate():
    """
    Generate .env.example from .env file.
    """
    generate_env_example()


@app.command()
def info():
    """
    Show project information.
    
    Display detected project type and basic info.
    """
    
    
    console.print("[bold cyan]Project Information[/bold cyan]\n")
    
    project_name = get_project_name()
    console.print(f"[green]Type:[/green] {project_name}")
    console.print(f"[green]Location:[/green] {Path.cwd()}")
    console.print(f"[green]Devnix:[/green] v{__version__}")


if __name__ == "__main__":
    app()

