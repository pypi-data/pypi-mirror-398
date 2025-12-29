"""
Template management system for the README generator.

This module handles loading and managing Jinja2 templates for different README styles.
"""

from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, Template


# Template descriptions for user guidance
TEMPLATE_DESCRIPTIONS = {
    "minimal": "A clean, minimal README with essential sections only",
    "standard": "A comprehensive README with all common sections",
    "fancy": "A rich README with badges, tables, and advanced formatting",
}


def get_available_templates() -> List[str]:
    """Get list of available template names."""
    return list(TEMPLATE_DESCRIPTIONS.keys())


def get_template_description(template_name: str) -> str:
    """Get description for a template."""
    return TEMPLATE_DESCRIPTIONS.get(template_name, "Unknown template")


def get_template_path(template_name: str) -> Optional[Path]:
    """Get the file path for a template."""
    # Get the path to the templates directory
    current_dir = Path(__file__).parent
    templates_dir = current_dir / "templates"
    
    template_file = templates_dir / f"{template_name}.md.j2"
    
    if template_file.exists():
        return template_file
    return None


def load_template(template_name: str) -> Optional[Template]:
    """Load a Jinja2 template by name with improved error handling."""
    # First try PackageLoader (works better for installed packages)
    try:
        from jinja2 import PackageLoader
        env = Environment(
            loader=PackageLoader('readme_generator', 'templates')
        )
        return env.get_template(f"{template_name}.md.j2")
    except Exception:
        # Fallback to FileSystemLoader for development
        template_path = get_template_path(template_name)
        
        if template_path is None:
            return None
        
        try:
            env = Environment(
                loader=FileSystemLoader(str(template_path.parent))
            )
            return env.get_template(template_path.name)
        except Exception:
            return None


def render_template(template_name: str, context: Dict) -> Optional[str]:
    """Render a template with the given context."""
    template = load_template(template_name)
    
    if template is None:
        return None
    
    try:
        return template.render(**context)
    except Exception:
        return None
