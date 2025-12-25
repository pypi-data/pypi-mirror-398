"""Project health and safety checks."""

import sys
import subprocess
from pathlib import Path

from rich.console import Console
from rich.table import Table

from devnix.utils import is_venv_active, find_venv, find_git_root, is_port_available, run_cmd_output


console = Console()


def run_doctor():
    """
    Run comprehensive health checks on the project.
    Checks Python version, venv, .env, git secrets, dependencies, and ports.
    """
    console.print("[bold cyan]Devnix Doctor - Project Health Check[/bold cyan]\n")
    
    checks = [
        _check_python,
        _check_venv,
        _check_env,
        _check_git_secrets,
        _check_dependencies,
        _check_ports,
    ]
    
    results = []
    for check in checks:
        result = check()
        if result:
            results.append(result)
    
    # Summary
    console.print()
    passed = sum(1 for r in results if r[0] == "PASS")
    warnings = sum(1 for r in results if r[0] == "WARN")
    failed = sum(1 for r in results if r[0] == "FAIL")
    
    if failed == 0 and warnings == 0:
        console.print("[bold green]All checks passed! Project is healthy.[/bold green]")
    elif failed == 0:
        console.print(f"[yellow]{warnings} warning(s) found. Review above.[/yellow]")
    else:
        console.print(f"[red]{failed} issue(s) found. Please fix them.[/red]")


def _check_python() -> tuple[str, str]:
    """Check Python version compatibility."""
    version = sys.version_info
    
    if version.major == 3 and version.minor >= 9:
        msg = f"Python {version.major}.{version.minor}.{version.micro} OK"
        console.print(f"[green]{msg}[/green]")
        return ("PASS", msg)
    else:
        msg = f"Python {version.major}.{version.minor} (3.9+ recommended)"
        console.print(f"[yellow]{msg}[/yellow]")
        return ("WARN", msg)


def _check_venv() -> tuple[str, str]:
    """Check virtual environment status."""
    if is_venv_active():
        msg = "Virtual environment active"
        console.print(f"[green]{msg}[/green]")
        return ("PASS", msg)
    else:
        venv = find_venv()
        if venv:
            msg = f"Virtual environment found ({venv.name}) but not active"
            console.print(f"[yellow]{msg}[/yellow]")
            return ("WARN", msg)
        else:
            msg = "No virtual environment detected"
            console.print(f"[yellow]{msg}[/yellow]")
            return ("WARN", msg)


def _check_env() -> tuple[str, str]:
    """Check .env file and critical variables."""
    env_file = Path.cwd() / ".env"
    
    if not env_file.exists():
        msg = ".env file missing"
        console.print(f"[red]{msg}[/red]")
        return ("FAIL", msg)
    
    # Read .env and check for critical variables
    try:
        content = env_file.read_text()
        
        # Check for DEBUG=True (unsafe for production)
        if "DEBUG=True" in content or "DEBUG = True" in content:
            msg = ".env found but DEBUG=True (unsafe for production)"
            console.print(f"[yellow]{msg}[/yellow]")
            return ("WARN", msg)
        
        # Check for SECRET_KEY or similar
        has_secret = any(key in content for key in ["SECRET_KEY", "API_KEY", "DATABASE_URL"])
        
        if has_secret:
            msg = ".env file found with secrets"
            console.print(f"[green]{msg}[/green]")
            return ("PASS", msg)
        else:
            msg = ".env found but no secrets detected"
            console.print(f"[yellow]{msg}[/yellow]")
            return ("WARN", msg)
            
    except Exception as e:
        msg = f".env file error: {e}"
        console.print(f"[red]{msg}[/red]")
        return ("FAIL", msg)


def _check_git_secrets() -> tuple[str, str]:
    """Check if secrets are committed to git."""
    git_root = find_git_root()
    
    if not git_root:
        msg = "Not a git repository (skipping secret check)"
        console.print(f"[dim]{msg}[/dim]")
        return ("INFO", msg)
    
    # Search for common secret patterns in git
    secret_patterns = [
        "SECRET_KEY",
        "API_KEY", 
        "PASSWORD",
        "PRIVATE_KEY",
        "AWS_SECRET",
    ]
    
    found_secrets = []
    for pattern in secret_patterns:
        exit_code, output = run_cmd_output(f'git grep -i "{pattern}"', cwd=git_root)
        if exit_code == 0 and output.strip():
            # Filter out comments and .env.example
            lines = [l for l in output.split('\n') if l and '.env.example' not in l and not l.strip().startswith('#')]
            if lines:
                found_secrets.append(pattern)
    
    if found_secrets:
        msg = f"Possible secrets in git: {', '.join(found_secrets)}"
        console.print(f"[red]{msg}[/red]")
        console.print(f"[dim]  Review and remove sensitive data from git history[/dim]")
        return ("FAIL", msg)
    else:
        msg = "No secrets found in git"
        console.print(f"[green]{msg}[/green]")
        return ("PASS", msg)


def _check_dependencies() -> tuple[str, str]:
    """Check if dependency files exist."""
    cwd = Path.cwd()
    
    if (cwd / "requirements.txt").exists():
        msg = "Dependencies found (requirements.txt)"
        console.print(f"[green]{msg}[/green]")
        return ("PASS", msg)
    elif (cwd / "pyproject.toml").exists():
        msg = "Dependencies found (pyproject.toml)"
        console.print(f"[green]{msg}[/green]")
        return ("PASS", msg)
    elif (cwd / "Pipfile").exists():
        msg = "Dependencies found (Pipfile)"
        console.print(f"[green]{msg}[/green]")
        return ("PASS", msg)
    else:
        msg = "No dependency file found"
        console.print(f"[yellow]{msg}[/yellow]")
        return ("WARN", msg)


def _check_ports() -> tuple[str, str]:
    """Check if common development ports are available."""
    common_ports = [8000, 5000, 8080, 3000]
    busy_ports = [port for port in common_ports if not is_port_available(port)]
    
    if not busy_ports:
        msg = "Common ports available"
        console.print(f"[green]{msg}[/green]")
        return ("PASS", msg)
    else:
        msg = f"Ports in use: {', '.join(map(str, busy_ports))}"
        console.print(f"[yellow]{msg}[/yellow]")
        return ("WARN", msg)
