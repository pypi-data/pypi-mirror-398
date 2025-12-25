"""Project runners for different frameworks."""

import subprocess
import sys
from pathlib import Path

from rich.console import Console
from dotenv import load_dotenv

from devnix.detector import ProjectType, detect_project
from devnix.utils import is_venv_active, find_venv, is_port_available

console = Console()


def run_project():
    """
    Run the project based on detected type.
    Loads .env, checks virtual environment, and starts the appropriate server.
    """
    # Load .env file if it exists
    env_file = Path.cwd() / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        console.print("[dim]Loaded .env file[/dim]")
    
    # Check virtual environment
    if not is_venv_active():
        venv = find_venv()
        if venv:
            console.print(f"[yellow]Virtual environment found at {venv.name} but not active[/yellow]")
            console.print(f"[yellow]  Activate it with: source {venv}/bin/activate[/yellow]")
        else:
            console.print("[yellow]No virtual environment detected[/yellow]")
    else:
        console.print("[dim]Virtual environment active[/dim]")
    
    # Detect project type
    project_type = detect_project()
    
    if project_type == "unknown":
        console.print("[red]Cannot determine project type[/red]")
        console.print("[dim]Supported: Django (manage.py), FastAPI/Flask (main.py/app.py), Script (main.py)[/dim]")
        sys.exit(1)
    
    # Get the appropriate command
    python = sys.executable
    commands = {
        "django": (f"{python} manage.py runserver", 8000),
        "fastapi": (f"{python} -m uvicorn main:app --reload", 8000),
        "flask": (f"{python} -m flask run", 5000),
        "script": (f"{python} main.py", None),
        "package": (None, None),
    }

    
    cmd, default_port = commands.get(project_type, (None, None))
    
    if not cmd:
        console.print(f"[red]Don't know how to run {project_type} projects[/red]")
        sys.exit(1)
    
    # Check port availability for web frameworks
    if default_port:
        if not is_port_available(default_port):
            console.print(f"[yellow]Port {default_port} is already in use[/yellow]")
            console.print(f"[dim]  The server might fail to start[/dim]")
    
    # Run the command
    console.print(f"\n[bold green]Running {project_type.title()} project...[/bold green]")
    console.print(f"[dim]Command: {cmd}[/dim]\n")
    
    try:
        subprocess.run(cmd, shell=True, cwd=Path.cwd())
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Error running project: {e}[/red]")
        sys.exit(1)
