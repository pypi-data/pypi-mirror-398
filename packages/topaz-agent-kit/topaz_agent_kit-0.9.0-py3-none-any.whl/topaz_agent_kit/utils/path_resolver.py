"""
Path resolution utilities for scripts and services.

Provides functions to intelligently resolve paths based on execution context,
handling both repository root and project directory scenarios.
"""

from pathlib import Path
from typing import Optional


def find_repository_root(start_path: Path, max_levels: int = 10) -> Path:
    """
    Find repository root from any starting path.
    
    Looks for markers:
    - pyproject.toml (definitive marker)
    - projects/ directory (indicates repository structure)
    
    Args:
        start_path: Starting path to search from
        max_levels: Maximum number of parent directories to search
        
    Returns:
        Path to repository root
        
    Examples:
        >>> find_repository_root(Path("projects/ensemble"))
        Path("/Users/Nishoo/Developer/topaz-agent-kit")
        
        >>> find_repository_root(Path("/some/project"))
        Path("/some")  # Falls back to parent if not found
    """
    current = start_path.resolve()
    
    # Look for repository root (contains pyproject.toml or has projects/ subdirectory)
    for _ in range(max_levels):
        # Check for pyproject.toml (definitive marker)
        if (current / "pyproject.toml").exists():
            return current
        
        # Check if current directory contains a projects/ subdirectory
        if (current / "projects").exists() and (current / "projects").is_dir():
            return current
        
        # Stop if we've reached filesystem root
        if current == current.parent:
            break
        
        current = current.parent
    
    # Fallback: if start_path contains "projects/", extract repository root
    if "projects" in start_path.parts:
        projects_index = start_path.parts.index("projects")
        if projects_index > 0:
            return Path(*start_path.parts[:projects_index])
    
    # Last resort: return parent of start_path
    return start_path.parent


def resolve_script_path(
    path_str: str,
    project_name: Optional[str] = None,
    cwd: Optional[Path] = None
) -> Path:
    """
    Resolve a script path intelligently based on execution context.
    
    Handles paths that may be:
    - Absolute paths (returned as-is)
    - Relative to repository root (e.g., "projects/ensemble/data/...")
    - Relative to project directory (e.g., "data/...")
    
    If path starts with "projects/" and execution is from project_dir,
    automatically strips the "projects/{name}/" prefix.
    
    Args:
        path_str: Path string to resolve (may be relative or absolute)
        project_name: Optional project name (e.g., "ensemble") for path adjustment
        cwd: Optional current working directory (defaults to Path.cwd())
        
    Returns:
        Resolved absolute Path
        
    Examples:
        >>> # From repository root
        >>> resolve_script_path("projects/ensemble/data/db.db")
        Path("/repo/projects/ensemble/data/db.db")
        
        >>> # From project directory
        >>> resolve_script_path("projects/ensemble/data/db.db", project_name="ensemble")
        Path("/repo/projects/ensemble/data/db.db")  # Strips prefix if in project_dir
        
        >>> # Absolute path
        >>> resolve_script_path("/absolute/path/db.db")
        Path("/absolute/path/db.db")
    """
    path = Path(path_str)
    
    # If already absolute, return as-is
    if path.is_absolute():
        return path
    
    # Use provided cwd or current working directory
    if cwd is None:
        cwd = Path.cwd()
    else:
        cwd = Path(cwd).resolve()
    
    # Detect if we're in a project directory (has config/pipeline.yml)
    is_project_dir = (cwd / "config" / "pipeline.yml").exists()
    
    # If path starts with "projects/" and we're in project_dir
    if path.parts and path.parts[0] == "projects" and is_project_dir:
        # Try to detect project name from cwd if not provided
        if project_name is None and "projects" in cwd.parts:
            projects_idx = cwd.parts.index("projects")
            if projects_idx + 1 < len(cwd.parts):
                project_name = cwd.parts[projects_idx + 1]
        
        # If we have a project name and path matches, strip prefix
        if project_name and len(path.parts) >= 2 and path.parts[1] == project_name:
            # Strip "projects/{name}/" prefix and resolve from project_dir
            return cwd / Path(*path.parts[2:])
    
    # Default: resolve from current working directory
    return cwd / path


def detect_project_name(project_dir: Path) -> Optional[str]:
    """
    Detect project name from project directory path.
    
    Args:
        project_dir: Path to project directory
        
    Returns:
        Project name if found (e.g., "ensemble"), None otherwise
        
    Examples:
        >>> detect_project_name(Path("projects/ensemble"))
        "ensemble"
        
        >>> detect_project_name(Path("/some/other/path"))
        None
    """
    project_dir = project_dir.resolve()
    
    # Check if path contains "projects/"
    if "projects" in project_dir.parts:
        projects_idx = project_dir.parts.index("projects")
        if projects_idx + 1 < len(project_dir.parts):
            return project_dir.parts[projects_idx + 1]
    
    return None

