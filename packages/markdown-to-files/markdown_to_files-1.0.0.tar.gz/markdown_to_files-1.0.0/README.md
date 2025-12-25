# Markdown to File Structure Generator

Transform markdown project blueprints into actual files and directories with a single command.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![PRs](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)

## Features

- **Dual Format Support**: Works with both tree diagrams and bullet lists
- **Instant Project Generation**: Create entire project structures from markdown
- **Template Engine**: Use Jinja2 templates or built-in templates for file content
- **Variable Replacement**: Inject variables into file names and content
- **Dry Run Mode**: Preview what will be created without making changes
- **Validation**: Validate your structure files before generation
- **Snapshot Creation**: Generate markdown from existing directories
- **Cross-Platform**: Windows, macOS, and Linux compatible

## Quick Demo

```bash
# Define your project in markdown
cat > my_app.md << 'EOF'
my-app/
|
|-- src/
|   |-- main.py          # content:print("Hello World!")
|   |-- utils/
|       |-- helpers.py   # content:def greet(): return "Hi!"
|
|-- tests/
|   |-- test_main.py
|
|-- README.md            # content:# My Awesome App
EOF

# Generate the project
mdf generate my_app.md --output ./my_project
```

## Installation

### Using pip (Recommended)

```bash
pip install markdown-to-files
```

### From Source

```bash
# Clone the repository
git clone https://github.com/yourusername/markdown-to-files.git
cd markdown-to-files

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

## Usage

### Basic Command Structure

```bash
mdf <command> [options]
```

### Available Commands

| Command | Description |
|---------|-------------|
| `mdf generate` | Generate project from markdown |
| `mdf validate` | Validate markdown structure file |
| `mdf init` | Create a new template |
| `mdf snapshot` | Create markdown from existing directory |
| `mdf --help` | Show all commands and options |

## Markdown Formats

### Format 1: Tree Diagram (Recommended for readability)

```
my-project/
|
|-- src/
|   |-- main.py          # FastAPI entry point
|   |-- api/
|       |-- users.py     # User endpoints
|       |-- items.py     # Item endpoints
|
|-- tests/
|   |-- test_api.py      # API tests
|
|-- README.md            # template:readme
```

### Format 2: Bullet List (Traditional)

```
- my-project/
  - src/
    - main.py          # FastAPI entry point
    - api/
      - users.py       # User endpoints
      - items.py       # Item endpoints
  - tests/
    - test_api.py      # API tests
  - README.md          # template:readme
```

## File Content Options

### Static Content

```
- src/
  - config.py          # content:DEBUG = True\nAPI_KEY = "secret"
```

### Template with Variables

```
- src/
  - main.py            # template:fastapi_main vars:app_name:MyApp,version:1.0
```

### Built-in Templates

- `python_module`: Basic Python module template
- `python_class`: Python class template
- `readme`: README.md template with project info
- `python_gitignore`: Python .gitignore template

### Custom Templates

Place `.j2` files in `templates/` directory:

```jinja2
# templates/fastapi_main.j2
from fastapi import FastAPI

app = FastAPI(title="{{ app_name }}", version="{{ version }}")

@app.get("/")
async def root():
    return {"message": "{{ app_name }} API"}
```

## Project Structure with Variables

Use YAML frontmatter and variables:

```yaml
---
project_name: AwesomeProject
author: Jane Developer
version: 1.0.0
license: MIT
---
```

```
${project_name}/
|
|-- src/
|   |-- __init__.py     # content:__version__ = "${version}"
|   |-- main.py         # content:# ${project_name} by ${author}
|
|-- LICENSE             # content:${license} License
|-- README.md           # template:readme
```

## Complete Examples

### Example 1: FastAPI Backend

```yaml
---
project_name: fastapi-backend
description: A FastAPI backend service
---
```

```
fastapi-backend/
|
|-- src/
|   |-- main.py                # template:fastapi_main
|   |-- api/
|   |   |-- __init__.py
|   |   |-- v1/
|   |       |-- users.py       # content:# User management
|   |       |-- items.py       # content:# Item management
|   |
|   |-- core/
|   |   |-- config.py          # content:from pydantic_settings import BaseSettings
|   |   |-- security.py        # content:# Authentication logic
|   |
|   |-- models/
|       |-- user.py            # content:from sqlalchemy import Column, String
|
|-- tests/
|   |-- __init__.py
|   |-- test_api.py            # content:# API tests
|
|-- requirements.txt           # content:fastapi>=0.104.0\nsqlalchemy>=2.0.0
|-- .env.example               # content:DATABASE_URL=postgresql://
|-- .gitignore                 # template:python_gitignore
|-- Dockerfile                 # content:FROM python:3.11-slim
|-- README.md                  # template:readme
```

### Example 2: Data Science Project

```
data-science-project/
|
|-- notebooks/
|   |-- 01-exploration.ipynb   # content:# Data exploration
|   |-- 02-modeling.ipynb      # content:# Model training
|
|-- src/
|   |-- data/
|   |   |-- loader.py          # content:def load_data(): pass
|   |   |-- cleaner.py         # content:def clean_data(): pass
|   |
|   |-- features/
|   |   |-- engineering.py     # content:def create_features(): pass
|   |
|   |-- models/
|       |-- trainer.py         # content:def train_model(): pass
|
|-- data/
|   |-- raw/                   # Raw data
|   |-- processed/             # Processed data
|
|-- reports/
|   |-- figures/               # Generated plots
|   |-- paper.md               # Research paper
|
|-- requirements.txt           # content:pandas>=2.0\nscikit-learn>=1.0
|-- environment.yml            # Conda environment
|-- README.md                  # template:readme
```

## Advanced Usage

### Multiple Variable Sources

```bash
# Command line variables
mdf generate project.md -v "author=John" -v "version=2.0"

# Config file variables
mdf generate project.md --config settings.yaml

# Combined
mdf generate project.md --config base.yaml -v "environment=production"
```

### Dry Run (Preview)

```bash
# See what will be created without making changes
mdf generate complex_project.md --output ./output --dry-run
```

### Force Overwrite

```bash
# Overwrite existing files
mdf generate project.md --output ./existing_dir --force
```

### Verbose Mode

```bash
# See detailed output including file contents
mdf generate project.md --output ./output --verbose
```

### Create Template

```bash
# Create a reusable template
mdf init fastapi-project --author "Your Name" --license "MIT"
```

### Create Markdown from Existing Project

```bash
# Generate markdown from existing directory
mdf snapshot ./existing_project --output structure.md
```

## Project Structure (This Tool)

```
markdown-to-files/
├── cli.py                 # Command-line interface
├── mdf_parser.py          # Markdown parser (tree + bullet)
├── template_engine.py     # Template processor
├── file_writer.py         # File system operations
├── requirements.txt       # Python dependencies
├── templates/            # Custom templates
│   ├── python_module.j2
│   ├── python_class.j2
│   ├── readme.j2
│   └── python_gitignore.j2
├── examples/             # Example markdown files
│   ├── fastapi_project.md
│   ├── data_science.md
│   └── python_package.md
└── tests/               # Test suite
    ├── test_parser.py
    └── test_cli.py
```

## Development

### Setup Development Environment

```bash
# Clone and setup
git clone https://github.com/yourusername/markdown-to-files.git
cd markdown-to-files

# Create virtual environment
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt
pip install -e .
pip install pytest pytest-cov black flake8
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. tests/

# Run specific test
pytest tests/test_parser.py -v
```

### Code Style

- Follow PEP 8 guidelines
- Use type hints for function signatures
- Write docstrings for public functions
- Keep functions focused and small

## Contributing

We welcome contributions! Here's how:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

See `CONTRIBUTING.md` for detailed guidelines.

### Development Workflow

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate

# 2. Install in development mode
pip install -e .

# 3. Make changes and test
pytest

# 4. Format code
black cli.py mdf_parser.py

# 5. Lint code
flake8 cli.py mdf_parser.py

# 6. Run integration tests
python test_generation.py
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by project scaffolding tools like Yeoman, Cookiecutter, and Plop.js
- Built with [Click](https://click.palletsprojects.com/) for CLI interface
- Uses [Jinja2](https://jinja.palletsprojects.com/) for template rendering
- Thanks to all contributors and users

## Reporting Issues

Found a bug or have a feature request? Please [open an issue](https://github.com/yourusername/markdown-to-files/issues) with:

- Description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version)

## Community

- [Documentation](https://github.com/yourusername/markdown-to-files/wiki)
- [Issue Tracker](https://github.com/yourusername/markdown-to-files/issues)
- [Discussions](https://github.com/yourusername/markdown-to-files/discussions)
- [PyPI Package](https://pypi.org/project/markdown-to-files/)

## Quick Start Examples

### Example 1: Create a Python Package

```bash
# Create package structure
cat > python_pkg.md << 'EOF'
mypackage/
|
|-- src/
|   |-- mypackage/
|       |-- __init__.py     # content:__version__ = "0.1.0"
|       |-- core.py         # content:def hello(): return "Hello"
|       |-- utils.py        # content:def helper(): pass
|
|-- tests/
|   |-- test_core.py        # content:from mypackage.core import hello
|
|-- .gitignore             # template:python_gitignore
|-- pyproject.toml         # content:[build-system]
|-- README.md              # template:readme
EOF

# Generate it
mdf generate python_pkg.md --output ./mypackage
```

### Example 2: Create a Web Project

```bash
# Create web project
mdf init web-project --description "Full-stack web application"

# Generate from template
mdf generate templates/web-project/structure.md --config templates/web-project/config.yaml --output ./mywebapp
```

### Example 3: Document Existing Project

```bash
# Create markdown from existing project
mdf snapshot ./my-existing-project --output documentation.md

# Now you can regenerate the structure anytime!
mdf generate documentation.md --output ./regenerated-project
```

## Support

If you find this tool useful, please give it a star on GitHub!

## Need Help?

Check out these resources:

- [Examples Directory](examples/) - Real-world usage examples
- [FAQ](docs/FAQ.md) - Frequently asked questions
- [Troubleshooting Guide](docs/TROUBLESHOOTING.md) - Common issues and solutions

---

Happy scaffolding!