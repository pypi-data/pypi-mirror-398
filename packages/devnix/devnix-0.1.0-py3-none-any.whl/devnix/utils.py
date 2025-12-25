"""Utility functions for Devnix."""

import subprocess
import sys
import socket
from pathlib import Path
from typing import Optional


def run_cmd(cmd: str, cwd: Optional[Path] = None) -> int:
    """
    Run a shell command and return the exit code.
    
    Args:
        cmd: Command to run
        cwd: Working directory (defaults to current directory)
        
    Returns:
        Exit code (0 for success)
    """
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.returncode
    except Exception:
        return 1


def run_cmd_output(cmd: str, cwd: Optional[Path] = None) -> tuple[int, str]:
    """
    Run a shell command and return exit code and output.
    
    Args:
        cmd: Command to run
        cwd: Working directory
        
    Returns:
        Tuple of (exit_code, output)
    """
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        return result.returncode, result.stdout
    except Exception as e:
        return 1, str(e)


def is_venv_active() -> bool:
    """Check if a virtual environment is currently active."""
    return (
        hasattr(sys, 'real_prefix') or
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    )


def find_venv() -> Optional[Path]:
    """Find virtual environment directory in current project."""
    cwd = Path.cwd()
    common_venv_names = ['venv', 'env', '.venv', 'ENV']
    
    for name in common_venv_names:
        venv_path = cwd / name
        if venv_path.exists() and venv_path.is_dir():
            # Check if it looks like a venv
            if (venv_path / 'bin' / 'python').exists() or (venv_path / 'Scripts' / 'python.exe').exists():
                return venv_path
    
    return None


def is_port_available(port: int, host: str = '127.0.0.1') -> bool:
    """
    Check if a port is available.
    
    Args:
        port: Port number to check
        host: Host address
        
    Returns:
        True if port is available, False otherwise
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex((host, port))
            return result != 0
    except Exception:
        return False


def find_git_root() -> Optional[Path]:
    """Find the root of the git repository."""
    cwd = Path.cwd()
    
    # Walk up the directory tree
    for parent in [cwd] + list(cwd.parents):
        if (parent / '.git').exists():
            return parent
    
    return None


def file_contains(filepath: Path, search_string: str) -> bool:
    """
    Check if a file contains a specific string.
    
    Args:
        filepath: Path to file
        search_string: String to search for
        
    Returns:
        True if string is found, False otherwise
    """
    try:
        if not filepath.exists():
            return False
        content = filepath.read_text(encoding='utf-8', errors='ignore')
        return search_string in content
    except Exception:
        return False
