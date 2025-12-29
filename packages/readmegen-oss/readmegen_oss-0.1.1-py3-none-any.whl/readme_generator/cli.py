"""
CLI interface for the AI-Powered GitHub README Generator.

This module provides the command-line interface using typer, with interactive
prompts for project details and template selection.
"""

import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.prompt import Confirm
from rich.panel import Panel
from rich.syntax import Syntax
import questionary
import traceback
import sys

from .generator import generate_readme
from .templates import get_available_templates, get_template_description
from .utils import validate_project_name, validate_description

app = typer.Typer(
    help="AI-Powered GitHub README Generator", rich_markup_mode="rich"
)


console = Console()


def handle_error(error: Exception, context: str = "operation"):
    """Handle errors with clear, user-friendly messages."""
    error_type = type(error).__name__
    
    # Provide specific error messages for common issues
    if isinstance(error, FileNotFoundError):
        console.print("[red]❌ File Error:[/red] Template files not found")
        console.print("💡 Check templates/ directory exists")
    elif isinstance(error, PermissionError):
        console.print("[red]❌ Permission Error:[/red] Cannot write to output file")
        console.print("💡 Check file permissions and try again")
    elif isinstance(error, ValueError):
        console.print("[red]❌ Input Error:[/red] Invalid input provided")
        console.print("💡 Please check your input and try again")
    elif isinstance(error, KeyError):
        console.print("[red]❌ Configuration Error:[/red] Missing template")
        console.print("💡 This appears to be a system configuration issue")
    else:
        # Generic error with context
        console.print(f"[red]❌ {context.title()} Failed:[/red] {error}")
        console.print(f"💡 {context} could not be completed due to an unexpected error")
    
    console.print("\n🔧 Debug Info:")
    console.print(f"   Error Type: {error_type}")
    console.print(f"   Context: {context}")
    
    # For development/debugging, show full traceback
    if "--debug" in sys.argv or "-v" in sys.argv:
        console.print("\n🐛 Full Traceback:")
        console.print(Syntax(traceback.format_exc(), "python", theme="monokai"))
    
    console.print("\n💡 If this problem persists, please report it at:")
    console.print("   https://github.com/your-username/ReadmeGen/issues")
    
    raise typer.Exit(code=1)

# Template preview snippets for user guidance
TEMPLATE_PREVIEWS = {
    "minimal": (
        "# Project Name\n\nBrief description\n\n## Features\n"
        "- Feature 1\n- Feature 2\n\n## Usage\n\n## License"
    ),
    "standard": (
        "# Project Name\n\nBrief description\n\n## Table of Contents\n"
        "## Features\n## Installation\n## Usage\n## Contributing\n## License"
    ),
    "fancy": (
        "# Project Name\n\n[![Badge]]()\n\nBrief description\n\n"
        "## ✨ Features\n## 🚀 Quick Start\n## 🛠️ Installation\n"
        "## 💻 Usage\n## 🧪 Testing\n## 🤝 Contributing\n## 📜 License"
    ),
}


def get_smart_defaults():
    """Get smart defaults for project information."""
    return {
        "project_name": Path.cwd().name,
        "template": "standard",
        "license": "MIT",
        "ai_enabled": False,
        "github_enabled": False
    }

@app.command()
def generate(
    project_name: Optional[str] = typer.Option(
        None, "--name", "-n", help="Project name"
    ),
    description: Optional[str] = typer.Option(
        None, "--description", "-d", help="Project description"
    ),
    template: Optional[str] = typer.Option(
        None, "--template", "-t", help="Template to use (minimal, standard, fancy)"
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output file path (default: README.md)"
    ),
    ai_enabled: bool = typer.Option(False, "--ai", help="Enable AI content enhancement"),
    github_enabled: bool = typer.Option(
        False, "--github", help="Enable GitHub metadata fetching"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing README.md file")
):
    """
    Generate a professional README file for your project.
    
    Interactive prompts will guide you through the process if options are not provided.
    """
    
    # Show welcome message with ASCII art
    console.print(Panel.fit(
        "[bold magenta]ReadmeGen 🚀[/bold magenta]\n"
        "Zero-friction README generation for developers",
        border_style="magenta"
    ))
    
    # Collect project information with smart defaults
    defaults = get_smart_defaults()
    
    # Use provided values or smart defaults
    if not project_name:
        project_name = defaults["project_name"]
    if not template:
        template = defaults["template"]
    
    project_info = collect_project_info(
        project_name=project_name,
        description=description,
        template=template
    )
    
    # Set output path
    if output is None:
        output = Path("README.md")
    
    # Check if file exists and handle overwrite
    if output.exists() and not force:
        if not Confirm.ask("README.md already exists. Overwrite?", default=False):
            console.print("[yellow]Generation cancelled.[/yellow]")
            raise typer.Exit()
    
    # Generate README with progress tracking
    try:
        steps = ["Setting up project info", "Rendering template", "Writing README.md"]

        with console.status("[bold green]Generating README...") as status:
            for step in steps:
                status.update(
                    f"[bold green]Generating README...[/bold green] [dim]({step})[/dim]"
                )
                # Small delay to show progress
                import time

                time.sleep(0.1)
        
        generate_readme(
            project_info=project_info,
            template_name=project_info["template"],
            output_path=output,
            ai_enabled=ai_enabled,
            github_enabled=github_enabled,
        )
        
        console.print("\n[green]✅ README generated successfully![/green]")
        console.print(f"📁 Output: {output.absolute()}")

        if ai_enabled:
            console.print("🤖 AI content enhancement was enabled")
        if github_enabled:
            console.print("🔗 GitHub metadata fetching was enabled")
            
    except Exception as e:
        console.print(f"[red]❌ Error generating README: {e}[/red]")
        raise typer.Exit(code=1)

@app.command()
def templates():
    """List available README templates with previews."""
    templates = get_available_templates()

    console.print("\n[bold]Available Templates:[/bold]\n")

    for template_name in templates:
        description = get_template_description(template_name)
        preview = TEMPLATE_PREVIEWS.get(template_name, "")
        console.print(f"• [bold]{template_name}[/bold]: {description}")
        if preview:
            preview_text = preview[:60] + "..." if len(preview) > 60 else preview
            console.print(f"  Preview: {preview_text}")
        else:
            console.print("  Preview: No preview available")
        console.print()

@app.command()
def init():
    """Initialize a new project with a README using interactive prompts."""
    console.print(Panel.fit(
        "[bold magenta]ReadmeGen 🚀[/bold magenta]\n"
        "Let's set up your project with a professional README!",
        border_style="magenta"
    ))
    
    # Collect project information interactively
    project_info = collect_project_info_interactive()
    
    # Generate README
    try:
        generate_readme(
            project_info=project_info,
            template_name=project_info["template"],
            output_path=Path("README.md"),
            ai_enabled=project_info.get("ai_enabled", False),
            github_enabled=project_info.get("github_enabled", False)
        )
        
        console.print("\n[green]✅ Project initialized successfully![/green]")
        console.print("📁 README.md has been created")
        console.print("\n💡 Tip: Use 'readmegen generate --ai' to enhance your README with AI!")
        
    except Exception as e:
        console.print(f"[red]❌ Error initializing project: {e}[/red]")
        raise typer.Exit(code=1)

def collect_project_info_interactive() -> dict:
    """Collect project information through interactive dropdowns and smart defaults."""
    defaults = get_smart_defaults()
    
    # Project name with smart default
    project_name_input = questionary.text(
        "Project Name:",
        default=defaults["project_name"],
        validate=lambda x: validate_project_name(x) or "Invalid project name",
    ).ask()

    project_name = project_name_input or defaults["project_name"]

    # Project description
    description_input = questionary.text(
        "Brief project description:",
        default="A brief description of your project",
        validate=lambda x: validate_description(x) or "Description cannot be empty",
    ).ask()

    description = description_input or "A brief description of your project"

    # Template selection with preview
    available_templates = get_available_templates()
    template_choices = []
    for template_name in available_templates:
        description_text = get_template_description(template_name)
        preview = TEMPLATE_PREVIEWS.get(template_name, "")
        if preview:
            preview_text = (
                f"\n  Preview: {preview[:50]}..."
                if len(preview) > 50
                else f"\n  Preview: {preview}"
            )
        else:
            preview_text = ""
        template_choices.append(
            questionary.Choice(
                f"{template_name} - {description_text}{preview_text}",
                value=template_name,
            )
        )

    template = questionary.select(
        "Select a template:", choices=template_choices, default=defaults["template"]
    ).ask()

    # License selection
    license_choices = [
        questionary.Choice("MIT - Permissive", value="MIT"),
        questionary.Choice("Apache 2.0 - Business-friendly", value="Apache 2.0"),
        questionary.Choice("GPL 3.0 - Copyleft", value="GPL 3.0"),
        questionary.Choice("BSD 3-Clause - Simple", value="BSD 3-Clause"),
        questionary.Choice("None - No license", value=None),
    ]

    license_choice = questionary.select(
        "Choose a license:", choices=license_choices, default=defaults["license"]
    ).ask()

    # AI enhancement toggle
    ai_enabled = questionary.confirm(
        "Enable AI content enhancement? (Optional - requires OpenAI API key)", default=False
    ).ask()

    # GitHub metadata toggle
    github_enabled = questionary.confirm(
        "Enable GitHub metadata fetching? (Optional - requires GitHub token)", default=False
    ).ask()

    # Features (optional)
    features = []
    if questionary.confirm("Would you like to add project features?", default=True).ask():
        while True:
            feature_input = questionary.text(
                "Add a feature (or press Enter to skip):"
            ).ask()
            if not feature_input:
                break
            features.append(feature_input)

    # Usage example (optional)
    usage_example = ""
    if questionary.confirm("Would you like to add a usage example?", default=False).ask():
        usage_example_input = questionary.text("Usage example:").ask()
        usage_example = usage_example_input or ""

    return {
        "project_name": project_name,
        "description": description,
        "template": template,
        "features": features,
        "usage_example": usage_example,
        "license": license_choice,
        "ai_enabled": ai_enabled,
        "github_enabled": github_enabled
    }


def collect_project_info(
    project_name: Optional[str] = None,
    description: Optional[str] = None,
    template: Optional[str] = None
) -> dict:
    """Collect project information - maintains backward compatibility with typer prompts."""
    
    # Use smart defaults when no values provided
    defaults = get_smart_defaults()
    if not project_name:
        project_name = defaults["project_name"]
    if not template:
        template = defaults["template"]

    # Project name validation
    while not validate_project_name(project_name):
        console.print(
            "[red]Invalid project name. Please use alphanumeric characters, "
            "spaces, hyphens, or underscores.[/red]"
        )
        project_name_input = questionary.text(
            "Project name:", default=project_name
        ).ask()
        project_name = project_name_input or project_name

    # Project description
    if not description:
        description = "A brief description of your project"

    while not validate_description(description):
        console.print("[red]Description cannot be empty.[/red]")
        description_input = questionary.text(
            "Brief project description:", default=description
        ).ask()
        description = description_input or description
    
    # Template selection
    available_templates = get_available_templates()
    if template not in available_templates:
        template = defaults["template"]
    
    # Additional project details (minimal for backward compatibility)
    features = []
    usage_example = ""
    license_choice = defaults["license"]
    
    return {
        "project_name": project_name,
        "description": description,
        "template": template,
        "features": features,
        "usage_example": usage_example,
        "license": license_choice
    }

if __name__ == "__main__":
    app()
