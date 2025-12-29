"""
Tests for the README generator functionality.
"""

from pathlib import Path
import tempfile

from readme_generator.generator import (
    generate_readme,
    prepare_template_context
)
from readme_generator.templates import render_template


class TestGenerator:
    """Test cases for the README generator."""
    
    def test_prepare_template_context(self):
        """Test template context preparation."""
        project_info = {
            "project_name": "Test Project",
            "description": "A test project",
            "features": ["Feature 1", "Feature 2"],
            "usage_example": "python main.py",
            "license": "MIT"
        }
        
        context = prepare_template_context(
            project_info, ai_enabled=False, github_enabled=False
        )
        
        assert context["project_name"] == "Test Project"
        assert context["description"] == "A test project"
        assert context["features"] == ["Feature 1", "Feature 2"]
        assert context["usage_example"] == "python main.py"
        assert context["license"] == "MIT"
        assert not context["ai_enabled"]
        assert not context["github_enabled"]
    
    def test_render_minimal_template(self):
        """Test rendering the minimal template."""
        context = {
            "project_name": "Test Project",
            "description": "A test project for README generation",
            "features": ["Feature 1", "Feature 2"],
            "usage_example": "python main.py",
            "license": "MIT"
        }
        
        rendered = render_template("minimal", context)
        
        assert rendered is not None
        assert "# Test Project" in rendered
        assert "A test project for README generation" in rendered
        assert "## Features" in rendered
        assert "- Feature 1" in rendered
        assert "- Feature 2" in rendered
        assert "## Usage" in rendered
        assert "python main.py" in rendered
        assert "## License" in rendered
        assert "MIT" in rendered
    
    def test_render_standard_template(self):
        """Test rendering the standard template."""
        context = {
            "project_name": "Test Project",
            "description": "A test project for README generation",
            "features": ["Feature 1", "Feature 2"],
            "usage_example": "python main.py",
            "license": "MIT"
        }
        
        rendered = render_template("standard", context)
        
        assert rendered is not None
        assert "# Test Project" in rendered
        assert "## Table of Contents" in rendered
        assert "## Features" in rendered
        assert "## Installation" in rendered
        assert "## Usage" in rendered
        assert "## Contributing" in rendered
        assert "## License" in rendered
    
    def test_render_fancy_template(self):
        """Test rendering the fancy template."""
        context = {
            "project_name": "Test Project",
            "description": "A test project for README generation",
            "features": ["Feature 1", "Feature 2"],
            "usage_example": "python main.py",
            "license": "MIT",
            "github_enabled": True,
            "github_url": "https://github.com/username/test-project"
        }
        
        rendered = render_template("fancy", context)
        
        assert rendered is not None
        assert "# Test Project" in rendered
        assert "## ✨ Features" in rendered
        assert "## 🚀 Quick Start" in rendered
        assert "## 🛠️ Installation" in rendered
        assert "## 💻 Usage" in rendered
        assert "## 🧪 Testing" in rendered
        assert "## 🤝 Contributing" in rendered
        assert "## 📜 License" in rendered
    
    def test_generate_readme_to_file(self):
        """Test generating a README file."""
        project_info = {
            "project_name": "Test Project",
            "description": "A test project for README generation",
            "template": "minimal",
            "features": ["Feature 1", "Feature 2"],
            "usage_example": "python main.py",
            "license": "MIT"
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "README.md"
            
            success = generate_readme(
                project_info=project_info,
                template_name="minimal",
                output_path=output_path,
                ai_enabled=False,
                github_enabled=False
            )
            
            assert success is True
            assert output_path.exists()
            
            content = output_path.read_text()
            assert "# Test Project" in content
            assert "A test project for README generation" in content
            assert "## Features" in content
    
    def test_invalid_template(self):
        """Test handling of invalid template."""
        context = {
            "project_name": "Test Project",
            "description": "A test project"
        }
        
        rendered = render_template("nonexistent", context)
        assert rendered is None
    
    def test_empty_project_info(self):
        """Test handling of empty project info."""
        project_info = {}
        
        context = prepare_template_context(project_info)
        
        assert context["project_name"] == ""
        assert context["description"] == ""
        assert context["features"] == []
        assert context["usage_example"] == ""
        assert context["license"] == ""
