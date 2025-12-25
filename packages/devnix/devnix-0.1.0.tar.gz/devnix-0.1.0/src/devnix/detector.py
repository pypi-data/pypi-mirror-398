"""Project type detection for Devnix."""

from pathlib import Path
from typing import Literal

from devnix.utils import file_contains

ProjectType = Literal["django", "fastapi", "flask", "script", "package", "unknown"]


def detect_project() -> ProjectType:
    """
    Automatically detect the project type based on files and content.
    
    Returns:
        Project type as a string
    """
    root = Path.cwd()

    # Django: Check for manage.py
    if (root / "manage.py").exists():
        return "django"

    # FastAPI/Flask: Check main.py or app.py
    for filename in ["main.py", "app.py"]:
        filepath = root / filename
        if filepath.exists():
            # Check for FastAPI
            if file_contains(filepath, "FastAPI"):
                return "fastapi"
            
            # Check for Flask
            if file_contains(filepath, "Flask"):
                return "flask"
            
            # If it's main.py but no framework detected, it's a script
            if filename == "main.py":
                return "script"

    # Package: Check for pyproject.toml
    if (root / "pyproject.toml").exists():
        return "package"

    # Unknown project type
    return "unknown"


def get_project_name() -> str:
    """Get a friendly name for the detected project type."""
    project_type = detect_project()
    
    names = {
        "django": "Django",
        "fastapi": "FastAPI",
        "flask": "Flask",
        "script": "Python Script",
        "package": "Python Package",
        "unknown": "Unknown"
    }
    
    return names.get(project_type, "Unknown")
