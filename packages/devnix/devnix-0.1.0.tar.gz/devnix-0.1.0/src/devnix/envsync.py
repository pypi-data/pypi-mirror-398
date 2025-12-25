"""Environment variable synchronization and checking."""

from pathlib import Path
from typing import Set

from rich.console import Console
from rich.table import Table

console = Console()

# Common secret keywords
SECRET_KEYWORDS = [
    "SECRET",
    "KEY",
    "PASSWORD",
    "TOKEN",
    "API",
    "PRIVATE",
    "CREDENTIAL",
]


def parse_env_file(filepath: Path) -> dict[str, str]:
    """
    Parse an .env file and return key-value pairs.
    
    Args:
        filepath: Path to .env file
        
    Returns:
        Dictionary of environment variables
    """
    env_vars = {}
    
    if not filepath.exists():
        return env_vars
    
    try:
        content = filepath.read_text()
        for line in content.split('\n'):
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Parse KEY=VALUE
            if '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
    
    except Exception as e:
        console.print(f"[red]Error parsing {filepath.name}: {e}[/red]")
    
    return env_vars


def is_secret_key(key: str) -> bool:
    """Check if a key name suggests it contains a secret."""
    key_upper = key.upper()
    return any(keyword in key_upper for keyword in SECRET_KEYWORDS)


def check_env():
    """
    Check environment variables against .env.example.
    Detect missing variables and potential secrets.
    """
    console.print("[bold cyan]Devnix Env Check - Environment Variables[/bold cyan]\n")
    
    cwd = Path.cwd()
    env_file = cwd / ".env"
    example_file = cwd / ".env.example"
    
    # Check if .env exists
    if not env_file.exists():
        console.print("[red].env file not found[/red]")
        
        if example_file.exists():
            console.print("[yellow].env.example exists but .env is missing[/yellow]")
            console.print("[dim]  Copy .env.example to .env and fill in values[/dim]")
        
        return
    
    # Parse files
    env_vars = parse_env_file(env_file)
    example_vars = parse_env_file(example_file)
    
    console.print(f"[green]Found {len(env_vars)} variables in .env[/green]")
    
    if not example_file.exists():
        console.print("[yellow].env.example not found[/yellow]")
        console.print("[dim]  Generate it with: devnix env generate[/dim]\n")
        
        # Show secrets warning
        _check_secrets(env_vars)
        return
    
    console.print(f"[green]Found {len(example_vars)} variables in .env.example[/green]\n")
    
    # Compare variables
    env_keys = set(env_vars.keys())
    example_keys = set(example_vars.keys())
    
    missing_in_env = example_keys - env_keys
    extra_in_env = env_keys - example_keys
    
    # Report missing variables
    if missing_in_env:
        console.print(f"[red]Missing {len(missing_in_env)} variable(s) in .env:[/red]")
        for key in sorted(missing_in_env):
            console.print(f"  [red]* {key}[/red]")
        console.print()
    
    # Report extra variables
    if extra_in_env:
        console.print(f"[yellow]Extra {len(extra_in_env)} variable(s) in .env (not in .env.example):[/yellow]")
        for key in sorted(extra_in_env):
            console.print(f"  [yellow]* {key}[/yellow]")
        console.print()
    
    # Check for secrets
    _check_secrets(env_vars)
    
    # Summary
    if not missing_in_env and not extra_in_env:
        console.print("[bold green]All .env and .env.example are in sync![/bold green]")


def _check_secrets(env_vars: dict[str, str]):
    """Check for potential secrets in environment variables."""
    secrets = {k: v for k, v in env_vars.items() if is_secret_key(k)}
    
    if secrets:
        console.print(f"[yellow]Found {len(secrets)} potential secret(s):[/yellow]")
        
        table = Table(show_header=True, header_style="bold yellow")
        table.add_column("Variable")
        table.add_column("Has Value")
        
        for key, value in sorted(secrets.items()):
            has_value = "YES" if value and value != '""' and value != "''" else "NO"
            color = "green" if has_value == "YES" else "red"
            table.add_row(key, f"[{color}]{has_value}[/{color}]")
        
        console.print(table)
        console.print("[dim]Make sure these are not committed to git[/dim]\n")


def generate_env_example():
    """Generate .env.example from .env file."""
    console.print("[bold cyan]Generating .env.example[/bold cyan]\n")
    
    cwd = Path.cwd()
    env_file = cwd / ".env"
    example_file = cwd / ".env.example"
    
    if not env_file.exists():
        console.print("[red].env file not found[/red]")
        return
    
    env_vars = parse_env_file(env_file)
    
    # Create .env.example with empty values for secrets
    lines = []
    lines.append("# Environment variables for this project")
    lines.append("# Copy this file to .env and fill in the values\n")
    
    for key in sorted(env_vars.keys()):
        if is_secret_key(key):
            lines.append(f"{key}=")
        else:
            lines.append(f"{key}={env_vars[key]}")
    
    try:
        example_file.write_text('\n'.join(lines))
        console.print(f"[green]Generated .env.example with {len(env_vars)} variables[/green]")
        console.print(f"[dim]Secret values have been cleared[/dim]")
    except Exception as e:
        console.print(f"[red]Error writing .env.example: {e}[/red]")
