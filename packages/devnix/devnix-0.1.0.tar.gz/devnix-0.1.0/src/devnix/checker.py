"""Test and lint checker for Devnix."""

import time
from pathlib import Path

from rich.console import Console
from rich.table import Table

from devnix.utils import run_cmd

console = Console()


def run_check():
    """
    Run tests and linters in sequence.
    Stops on first failure.
    """
    console.print("[bold cyan]Devnix Check - Running Tests & Linters[/bold cyan]\n")
    
    tools = [
        ("pytest", "Running tests"),
        ("black --check .", "Checking code formatting"),
        ("isort --check-only .", "Checking import sorting"),
        ("flake8 .", "Linting code"),
    ]
    
    results = []
    
    for tool_cmd, description in tools:
        tool_name = tool_cmd.split()[0]
        
        # Check if tool is available
        if run_cmd(f"which {tool_name}") != 0:
            console.print(f"[dim]{tool_name} not installed (skipping)[/dim]")
            continue
        
        console.print(f"[cyan]{description}...[/cyan]")
        
        start_time = time.time()
        exit_code = run_cmd(tool_cmd)
        elapsed = time.time() - start_time
        
        if exit_code == 0:
            console.print(f"[green]{tool_name} passed[/green] [dim]({elapsed:.2f}s)[/dim]")
            results.append((tool_name, "PASS", elapsed))
        else:
            console.print(f"[red]{tool_name} failed[/red] [dim]({elapsed:.2f}s)[/dim]")
            results.append((tool_name, "FAIL", elapsed))
            
            console.print(f"\n[red]Stopping due to {tool_name} failure.[/red]")
            console.print(f"[dim]Fix the issues and run 'devnix check' again.[/dim]")
            return False
    
    # Summary
    if results:
        console.print("\n[bold green]All checks passed![/bold green]")
        
        # Show summary table
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Tool")
        table.add_column("Status")
        table.add_column("Time", justify="right")
        
        for tool, status, elapsed in results:
            status_color = "green" if status == "PASS" else "red"
            table.add_row(
                tool,
                f"[{status_color}]{status}[/{status_color}]",
                f"{elapsed:.2f}s"
            )
        
        console.print(table)
        return True
    else:
        console.print("[yellow]No tools found to run[/yellow]")
        console.print("[dim]Install pytest, black, isort, or flake8 to enable checks[/dim]")
        return False
