# ReadmeGen

[![PyPI version](https://badge.fury.io/py/readmegen-oss.svg)](https://badge.fury.io/py/readmegen-oss)
[![Python Version](https://img.shields.io/pypi/pyversions/readmegen-oss.svg)](https://pypi.org/project/readmegen-oss/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

AI-Powered GitHub README Generator - Zero-friction CLI for professional README files

## 🚀 Quick Start

**Install in one command:**
```bash
pip install readmegen-oss
```

**Generate a README in 60 seconds:**
```bash
readmegen init
```

That's it! ReadmeGen will guide you through creating a professional README with smart defaults and interactive prompts.

## 🎯 Features

### Zero-Friction Adoption
- **Single-line install**: `pip install readmegen-oss`
- **60-second setup**: Interactive prompts with smart defaults
- **No configuration needed**: Works out of the box
- **Professional results**: Generate GitHub-ready README files instantly

### Interactive CLI
- **Smart defaults**: Auto-detects project name, uses sensible defaults
- **Visual templates**: See template previews before selecting
- **Progress feedback**: Real-time progress during generation
- **Error handling**: Graceful failures with clear messages

### Three Professional Templates
- **Minimal**: Clean, essential sections only
- **Standard**: Comprehensive with table of contents, installation, usage
- **Fancy**: Rich formatting with badges, emojis, and advanced sections

## 📖 Usage

### Quick Setup (Recommended)
```bash
# Install
pip install readmegen-oss

# Initialize new project
readmegen init
```

### Generate README with Options
```bash
# Generate with specific options
readmegen generate --name "My Project" --description "A great project" --template standard

# Generate with AI enhancement (optional)
readmegen generate --name "My AI Project" --ai

# List available templates
readmegen templates
```

### CLI Options
- `--name, -n`: Project name (auto-detected from directory)
- `--description, -d`: Project description
- `--template, -t`: Template (minimal, standard, fancy) - default: standard
- `--output, -o`: Output file path - default: README.md
- `--ai`: Enable AI content enhancement (optional)
- `--github`: Enable GitHub metadata fetching (optional)
- `--force, -f`: Overwrite existing README.md

## 🎨 Templates

### Minimal Template
Perfect for simple projects that need just the essentials.

### Standard Template
Comprehensive template with all common sections: features, installation, usage, contributing, license.

### Fancy Template
Rich template with badges, tables, and advanced formatting for professional projects.

## 🏗️ Project Structure

```
readme_generator/
├── readme_generator/            # Core package
│   ├── __init__.py
│   ├── cli.py                   # CLI interface with interactive prompts
│   ├── generator.py             # Core README generation logic
│   ├── templates.py             # Template management system
│   ├── utils.py                 # Utility functions
│   └── templates/               # Jinja2 README templates
├── tests/                       # Unit tests
├── pyproject.toml               # Project configuration
└── README.md                    # This file
```

## 🧪 Testing

Run the test suite:
```bash
pytest
```

## 🔧 Development

### Setup
```bash
# Clone and install
git clone https://github.com/your-username/ReadmeGen.git
cd ReadmeGen
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .[dev]
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=readme_generator
```

## 📋 Roadmap

### Phase A: Distribution & Trust (Current)
- ✅ Polished CLI with interactive prompts
- ✅ Smart defaults and zero-config setup
- ✅ Professional templates with previews
- ✅ PyPI package ready for distribution

### Phase B: Trust & Adoption
- [ ] Comprehensive error handling
- [ ] Clear failure messages
- [ ] Deterministic output
- [ ] Demo materials and documentation

### Phase C: Power Unlocks (Future)
- [ ] AI content enhancement (optional)
- [ ] GitHub metadata fetching (optional)
- [ ] Configuration persistence

### Phase D: Surface Area Expansion (Future)
- [ ] Web UI interface
- [ ] README previews
- [ ] Team templates
- [ ] Org-level configs

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with ❤️ using Python, typer, questionary, and rich
- Inspired by the need for better README generation tools
- Thanks to all contributors and early adopters

---

**Made with** ❤️ **by the community, for the community**
