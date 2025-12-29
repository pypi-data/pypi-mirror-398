"""
Utility functions for the README generator.

This module contains helper functions for file operations, validation,
and other utility tasks.
"""

import re
from pathlib import Path
from typing import Optional


def validate_project_name(project_name: str) -> bool:
    """
    Validate project name format.
    
    Args:
        project_name: Name to validate
    
    Returns:
        True if valid, False otherwise
    """
    if not project_name or not project_name.strip():
        return False
    
    # Allow alphanumeric characters, spaces, hyphens, and underscores
    pattern = r'^[a-zA-Z0-9\s\-_]+$'
    return bool(re.match(pattern, project_name.strip()))


def validate_description(description: str) -> bool:
    """
    Validate project description.
    
    Args:
        description: Description to validate
    
    Returns:
        True if valid, False otherwise
    """
    return bool(description and description.strip())


def validate_output_path(output_path: Path) -> bool:
    """
    Validate output file path.
    
    Args:
        output_path: Path to validate
    
    Returns:
        True if valid, False otherwise
    """
    if output_path is None:
        return False
    
    # Check if parent directory exists or can be created
    parent_dir = output_path.parent
    return parent_dir.exists() or parent_dir.is_dir()


def write_file(file_path: Path, content: str) -> bool:
    """
    Write content to a file.
    
    Args:
        file_path: Path to the file
        content: Content to write
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    except Exception:
        return False


def read_file(file_path: Path) -> Optional[str]:
    """
    Read content from a file.
    
    Args:
        file_path: Path to the file
    
    Returns:
        File content as string, or None if file doesn't exist or can't be read
    """
    try:
        if not file_path.exists():
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return None


def format_license(license_name: Optional[str]) -> str:
    """
    Format license information for README.
    
    Args:
        license_name: License name
    
    Returns:
        Formatted license string
    """
    if not license_name:
        return ""
    
    # Common license abbreviations
    license_map = {
        "MIT": "MIT License",
        "Apache 2.0": "Apache License 2.0",
        "GPL 3.0": "GNU General Public License v3.0",
        "BSD 3-Clause": "BSD 3-Clause License",
    }
    
    return license_map.get(license_name, license_name)


def sanitize_filename(name: str) -> str:
    """
    Sanitize a string to be used as a filename.
    
    Args:
        name: String to sanitize
    
    Returns:
        Sanitized filename
    """
    # Replace spaces with hyphens and remove special characters
    sanitized = re.sub(r'[^\w\s-]', '', name.strip())
    sanitized = re.sub(r'[-\s]+', '-', sanitized)
    return sanitized.lower()
