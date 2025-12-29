"""
Core README generation logic.

This module contains the main functions for generating README files from templates
and project information.
"""

from pathlib import Path
from typing import Dict

from .templates import render_template
from .utils import write_file, validate_output_path


def generate_readme(
    project_info: Dict,
    template_name: str,
    output_path: Path,
    ai_enabled: bool = False,
    github_enabled: bool = False,
) -> bool:
    """
    Generate a README file from template and project information.
    
    Args:
        project_info: Dictionary containing project details
        template_name: Name of the template to use
        output_path: Path where the README should be saved
        ai_enabled: Whether to enable AI content enhancement
        github_enabled: Whether to enable GitHub metadata fetching
    
    Returns:
        True if generation was successful, False otherwise
    """
    # Validate output path
    if not validate_output_path(output_path):
        raise ValueError(f"Invalid output path: {output_path}")
    
    # Prepare context for template rendering
    context = prepare_template_context(project_info, ai_enabled, github_enabled)
    
    # Render template
    rendered_content = render_template(template_name, context)
    
    if rendered_content is None:
        raise ValueError(f"Failed to render template: {template_name}")
    
    # Write to file
    try:
        write_file(output_path, rendered_content)
        return True
    except Exception as e:
        raise RuntimeError(f"Failed to write README file: {e}") from e


def prepare_template_context(
    project_info: Dict, ai_enabled: bool = False, github_enabled: bool = False
) -> Dict:
    """
    Prepare the context dictionary for template rendering.
    
    Args:
        project_info: Dictionary containing project details
        ai_enabled: Whether AI features are enabled
        github_enabled: Whether GitHub features are enabled
    
    Returns:
        Dictionary with context variables for template rendering
    """
    # Basic project information
    context = {
        "project_name": project_info.get("project_name", ""),
        "description": project_info.get("description", ""),
        "features": project_info.get("features", []),
        "usage_example": project_info.get("usage_example", ""),
        "license": project_info.get("license", ""),
        "ai_enabled": ai_enabled,
        "github_enabled": github_enabled,
    }
    
    # Add optional GitHub metadata if enabled
    if github_enabled:
        github_metadata = fetch_github_metadata(
            project_info.get("project_name", "")
        )
        context.update(github_metadata)
    
    # Add AI-enhanced content if enabled
    if ai_enabled:
        ai_content = enhance_content_with_ai(project_info)
        context.update(ai_content)
    
    return context


def fetch_github_metadata(project_name: str) -> Dict:
    """
    Fetch GitHub repository metadata.
    
    Args:
        project_name: Name of the project
    
    Returns:
        Dictionary with GitHub metadata
    """
    # This is a placeholder for GitHub API integration
    # In Phase 2, this will fetch actual metadata from GitHub
    return {
        "github_url": (
            f"https://github.com/username/"
            f"{project_name.lower().replace(' ', '-')}"
        ),
        "stars": "⭐ 0",
        "forks": "🍴 0",
        "issues": "🐛 0",
    }


def enhance_content_with_ai(project_info: Dict) -> Dict:
    """
    Enhance project content using AI.
    
    Args:
        project_info: Dictionary containing project details
    
    Returns:
        Dictionary with AI-enhanced content
    """
    # This is a placeholder for AI integration
    # In Phase 2, this will use OpenAI API or similar for content enhancement
    description = project_info.get("description", "")
    features = project_info.get("features", [])

    return {
        "enhanced_description": description,
        "suggested_features": features,
        "ai_enhanced": False,  # Flag to indicate AI was used
    }
