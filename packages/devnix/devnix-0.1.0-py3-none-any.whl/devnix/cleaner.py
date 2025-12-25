"""Cache and junk file cleaner for Devnix."""

import shutil
from pathlib import Path

from rich.console import Console
from rich.prompt import Confirm

console = Console()

# Directories to clean
CACHE_DIRS = [
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    "htmlcov",
    ".coverage",
]

# Files to clean
CACHE_FILES = [
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".coverage",
]


def clean_project():
    """
    Clean Python cache files and directories.
    Asks before removing virtual environments.
    """
    console.print("[bold cyan]Devnix Clean - Removing Cache Files[/bold cyan]\n")
    
    cwd = Path.cwd()
    removed_dirs = []
    removed_files = []
    
    # Clean cache directories
    for path in cwd.rglob("*"):
        if path.is_dir() and path.name in CACHE_DIRS:
            try:
                shutil.rmtree(path)
                removed_dirs.append(path.name)
                console.print(f"[dim]Removed {path.relative_to(cwd)}[/dim]")
            except Exception as e:
                console.print(f"[yellow]Could not remove {path.name}: {e}[/yellow]")
    
    # Clean cache files
    for pattern in CACHE_FILES:
        for path in cwd.rglob(pattern):
            if path.is_file():
                try:
                    path.unlink()
                    removed_files.append(path.name)
                except Exception as e:
                    console.print(f"[yellow]Could not remove {path.name}: {e}[/yellow]")
    
    # Summary
    total_removed = len(set(removed_dirs)) + len(removed_files)
    
    if total_removed > 0:
        console.print(f"\n[green]Cleaned {len(set(removed_dirs))} cache directories and {len(removed_files)} files[/green]")
    else:
        console.print("\n[dim]No cache files found to clean[/dim]")
    
    # Ask about virtual environment
    venv_dirs = ["venv", "env", ".venv", "ENV"]
    found_venvs = [d for d in venv_dirs if (cwd / d).exists()]
    
    if found_venvs:
        console.print(f"\n[yellow]Found virtual environment(s): {', '.join(found_venvs)}[/yellow]")
        
        if Confirm.ask("Do you want to remove the virtual environment?", default=False):
            for venv in found_venvs:
                venv_path = cwd / venv
                try:
                    shutil.rmtree(venv_path)
                    console.print(f"[green]Removed {venv}[/green]")
                except Exception as e:
                    console.print(f"[red]Could not remove {venv}: {e}[/red]")
        else:
            console.print("[dim]Virtual environment kept[/dim]")
