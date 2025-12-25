#!/usr/bin/env python3
"""
Markdown to File Structure Generator
Usage: mdf <command> [options]
"""

import click
from pathlib import Path
import sys
import os
import yaml

from .parser import MDFParser
from .writer import FileWriter
from .templates import TemplateEngine

# Add color support
try:
    from colorama import Fore, Style, init
    init(autoreset=True)
    HAS_COLORS = True
except ImportError:
    class DummyColors:
        def __getattr__(self, name):
            return ''
    Fore = Style = DummyColors()
    HAS_COLORS = False

def print_success(msg):
    """Print success message"""
    if HAS_COLORS:
        click.echo(f"{Fore.GREEN}✓ {msg}{Style.RESET_ALL}")
    else:
        click.echo(f"✓ {msg}")

def print_error(msg):
    """Print error message"""
    if HAS_COLORS:
        click.echo(f"{Fore.RED}✗ {msg}{Style.RESET_ALL}")
    else:
        click.echo(f"✗ {msg}")

def print_warning(msg):
    """Print warning message"""
    if HAS_COLORS:
        click.echo(f"{Fore.YELLOW}⚠ {msg}{Style.RESET_ALL}")
    else:
        click.echo(f"⚠ {msg}")

def print_info(msg):
    """Print info message"""
    if HAS_COLORS:
        click.echo(f"{Fore.CYAN}ℹ {msg}{Style.RESET_ALL}")
    else:
        click.echo(f"ℹ {msg}")

@click.group()
@click.version_option(version='1.0.0', prog_name='Markdown File Generator')
def cli():
    """Convert Markdown project structures to actual files and directories
    
    Supports both tree diagram and bullet list formats.
    """
    pass

@cli.command()
@click.argument('markdown_file', type=click.Path(exists=True, dir_okay=False))
@click.option('--output', '-o', default='.', 
              help='Output directory (default: current directory)')
@click.option('--variables', '-v', multiple=True, 
              help='Variables in format key=value')
@click.option('--config', '-c', type=click.Path(exists=True, dir_okay=False), 
              help='YAML config file with variables')
@click.option('--dry-run', is_flag=True, 
              help='Show what would be created without making changes')
@click.option('--cleanup', is_flag=True, 
              help='Clean up created files after generation')
@click.option('--force', '-f', is_flag=True,
              help='Force overwrite of existing files')
@click.option('--verbose', is_flag=True,
              help='Show detailed output')
@click.option('--format', type=click.Choice(['auto', 'tree', 'bullet']), 
              default='auto', help='Force specific input format')
def generate(markdown_file, output, variables, config, dry_run, cleanup, 
             force, verbose, format):
    """Generate project structure from markdown file"""
    
    # Check output directory
    output_path = Path(output).resolve()
    if output_path.exists() and not output_path.is_dir():
        print_error(f"Output path exists and is not a directory: {output}")
        return 1
    
    # Load markdown with UTF-8 encoding
    try:
        with open(markdown_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print_error(f"Failed to read markdown file: {e}")
        return 1
    
    # Parse markdown
    parser = MDFParser()
    config_data, markdown_content = parser.parse_yaml_frontmatter(content)
    
    # Auto-detect or use specified format
    if format == 'auto':
        detected_format = parser.detect_format(markdown_content)
        if verbose:
            print_info(f"Auto-detected format: {detected_format}")
    else:
        detected_format = format
    
    # Parse structure based on format
    try:
        if detected_format == 'tree':
            structure_data = parser.parse_tree_syntax(markdown_content)
        else:
            structure_data = parser.parse_bullet_syntax(markdown_content)
    except Exception as e:
        print_error(f"Failed to parse markdown structure: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    # Merge variables
    all_vars = {}
    if config:
        try:
            with open(config, 'r', encoding='utf-8') as f:
                file_vars = yaml.safe_load(f) or {}
                all_vars.update(file_vars)
        except Exception as e:
            print_error(f"Failed to load config file: {e}")
            return 1
    
    all_vars.update(config_data)
    
    for var in variables:
        if '=' in var:
            key, value = var.split('=', 1)
            all_vars[key.strip()] = value.strip()
        else:
            print_warning(f"Ignoring invalid variable format: {var}")
    
    # Show structure preview
    click.echo(f"\n📁 Project Structure from: {Path(markdown_file).name}")
    click.echo("=" * 50)
    
    for item in structure_data['structure']:
        indent = "  " * item['depth']
        icon = "📁" if item['type'] == 'directory' else "📄"
        line = f"{indent}{icon} {item['full_path']}"
        
        # Add annotations
        annotations = []
        if item.get('template'):
            annotations.append(f"template:{item['template']}")
        if item.get('content'):
            content_preview = item['content'][:20] + "..." if len(item['content']) > 20 else item['content']
            annotations.append(f"content:{content_preview}")
        
        if annotations:
            line += f"  ({', '.join(annotations)})"
        
        click.echo(line)
    
    click.echo("=" * 50)
    
    # Show summary
    dirs = sum(1 for item in structure_data['structure'] if item['type'] == 'directory')
    files = sum(1 for item in structure_data['structure'] if item['type'] == 'file')
    click.echo(f"📊 Summary: {dirs} directories, {files} files")
    
    if dry_run:
        print_success("Dry run complete. No files created.")
        return 0
    
    # Check for existing files if not forcing
    if not force:
        conflicts = []
        for item in structure_data['structure']:
            item_path = output_path / item['full_path']
            if item_path.exists():
                conflicts.append(str(item_path.relative_to(output_path)))
        
        if conflicts:
            print_error(f"Found {len(conflicts)} existing files/directories:")
            for conflict in conflicts[:5]:
                print_error(f"  {conflict}")
            if len(conflicts) > 5:
                print_error(f"  ... and {len(conflicts) - 5} more")
            click.echo("\nUse --force to overwrite existing files.")
            return 1
    
    # Create files
    click.echo("\n🚀 Creating files...")
    try:
        writer = FileWriter(str(output_path))
        writer.force_overwrite = force
        writer.verbose = verbose
        
        created = writer.create_structure(structure_data['structure'], all_vars)
        
        if created:
            print_success(f"Created {len(created)} items in: {output_path}")
            
            # Show sample of created files
            if verbose and created:
                click.echo("\n📦 Sample of created files:")
                for item in sorted(created)[:10]:  # Show first 10
                    rel_path = Path(item).relative_to(output_path)
                    if Path(item).is_file():
                        click.echo(f"  📄 {rel_path}")
                
                if len(created) > 10:
                    click.echo(f"  ... and {len(created) - 10} more")
        
    except Exception as e:
        print_error(f"Failed to create structure: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    # Cleanup if requested
    if cleanup:
        click.echo("\n🧹 Cleaning up...")
        try:
            writer.cleanup()
            print_success("Cleanup complete")
        except Exception as e:
            print_error(f"Failed to cleanup: {e}")
    
    return 0

@cli.command()
@click.argument('template_name')
@click.option('--output', '-o', default='templates', 
              help='Output directory for template')
@click.option('--description', '-d', help='Template description')
@click.option('--author', '-a', default='Your Name', help='Author name')
@click.option('--license', '-l', default='MIT', help='License type')
def init(template_name, output, description, author, license):
    """Initialize a new markdown template"""
    
    template_dir = Path(output) / template_name
    
    # Check if template exists
    if template_dir.exists():
        if not click.confirm(f"Template '{template_name}' already exists. Overwrite?"):
            return 1
    
    # Create directories
    template_dir.mkdir(parents=True, exist_ok=True)
    
    # Default description
    if not description:
        description = f"A {template_name.replace('-', ' ')} project template"
    
    # Create sample structure (using ASCII tree for Windows compatibility)
    sample_md = template_dir / "structure.md"
    
    sample_content = f'''---
project_name: {template_name}
author: {author}
version: "1.0.0"
license: {license}
description: {description}
---

# {template_name.title()} Project Structure

## Tree Diagram Format

{template_name}/
|
|-- src/
|   |-- __init__.py
|   |-- main.py          # template:python_module
|   |-- utils/
|       |-- __init__.py
|       |-- helpers.py   # content:# Helper functions here
|
|-- tests/
|   |-- __init__.py
|   |-- test_main.py     # template:python_class vars:class_name:TestMain
|
|-- docs/
|   |-- README.md        # template:readme
|
|-- .gitignore           # template:python_gitignore
|-- pyproject.toml       # content:[build-system]
|-- README.md            # template:readme
|-- LICENSE              # content:{license} License

## Bullet List Format

- {template_name}/
  - src/
    - __init__.py
    - main.py          # template:python_module
    - utils/
      - __init__.py
      - helpers.py     # content:# Helper functions here
  - tests/
    - __init__.py
    - test_main.py     # template:python_class vars:class_name:TestMain
  - docs/
    - README.md        # template:readme
  - .gitignore         # template:python_gitignore
  - pyproject.toml     # content:[build-system]
  - README.md          # template:readme
  - LICENSE            # content:{license} License
'''
    
    sample_md.write_text(sample_content, encoding='utf-8')
    
    # Create template files directory
    templates_subdir = template_dir / "templates"
    templates_subdir.mkdir(exist_ok=True)
    
    # Create basic templates
    basic_templates = {
        'python_module.j2': '''"""
{{ module_name }}
{{ description }}
"""

def main():
    """Main entry point"""
    print("Hello from {{ module_name }}!")

if __name__ == "__main__":
    main()
''',
        'readme.j2': '''# {{ project_name }}

{{ description }}

## Installation

```bash
{{ install_command }}
```

## License

{{ license }}
'''
    }
    
    for filename, content in basic_templates.items():
        (templates_subdir / filename).write_text(content, encoding='utf-8')
    
    print_success(f"Template '{template_name}' created in {template_dir}")
    
    click.echo(f"\n📁 Template created at: {template_dir}")
    click.echo(f"📄 Structure file: {template_dir}/structure.md")
    click.echo(f"📂 Templates: {template_dir}/templates/")
    
    return 0

@cli.command()
@click.argument('structure_file', type=click.Path(exists=True, dir_okay=False))
@click.option('--verbose', '-v', is_flag=True, help='Show detailed validation')
def validate(structure_file, verbose):
    """Validate markdown structure file"""
    try:
        with open(structure_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print_error(f"Failed to read file: {e}")
        return 1
    
    parser = MDFParser()
    config, markdown_content = parser.parse_yaml_frontmatter(content)
    
    click.echo(f"📋 Validating: {Path(structure_file).name}")
    click.echo("=" * 50)
    
    # Check frontmatter
    if config:
        print_success(f"Frontmatter: {len(config)} variables found")
        if verbose:
            for key, value in config.items():
                click.echo(f"  {key}: {value}")
    else:
        print_warning("No frontmatter found")
    
    # Detect format
    detected_format = parser.detect_format(markdown_content)
    click.echo(f"Format: {detected_format}")
    
    # Parse structure
    try:
        if detected_format == 'tree':
            structure_data = parser.parse_tree_syntax(markdown_content)
        else:
            structure_data = parser.parse_bullet_syntax(markdown_content)
        
        items = structure_data['structure']
        
        if not items:
            print_error("No structure items found")
            return 1
        
        print_success(f"Structure: {len(items)} items parsed")
        
        # Analyze structure
        dirs = sum(1 for item in items if item['type'] == 'directory')
        files = sum(1 for item in items if item['type'] == 'file')
        
        click.echo(f"  Directories: {dirs}")
        click.echo(f"  Files: {files}")
        
        # Check for issues
        issues = []
        seen_paths = set()
        
        for item in items:
            if item['full_path'] in seen_paths:
                issues.append(f"Duplicate: {item['full_path']}")
            seen_paths.add(item['full_path'])
        
        if issues:
            click.echo(f"\n⚠ Issues found:")
            for issue in issues:
                print_warning(f"  {issue}")
        else:
            print_success("No issues found")
        
        print_success("✅ File is valid!")
        
        return 0
        
    except Exception as e:
        print_error(f"Validation failed: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return 1

@cli.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False))
@click.option('--output', '-o', type=click.Path(dir_okay=False),
              help='Output markdown file')
@click.option('--format', type=click.Choice(['tree', 'bullet']),
              default='bullet', help='Output format')
def snapshot(directory, output, format):
    """Create markdown from existing directory structure"""
    dir_path = Path(directory).resolve()
    
    if not dir_path.is_dir():
        print_error(f"Not a directory: {directory}")
        return 1
    
    # Collect structure
    structure = []
    
    for root, dirs, files in os.walk(dir_path):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        depth = len(Path(root).relative_to(dir_path).parts)
        
        # Add directories at this level
        for d in sorted(dirs):
            if not d.startswith('.'):  # Skip hidden
                structure.append({
                    'name': d,
                    'full_path': str(Path(root).relative_to(dir_path) / d),
                    'type': 'directory',
                    'depth': depth
                })
        
        # Add files at this level
        for f in sorted(files):
            if not f.startswith('.'):  # Skip hidden
                structure.append({
                    'name': f,
                    'full_path': str(Path(root).relative_to(dir_path) / f),
                    'type': 'file',
                    'depth': depth
                })
    
    # Generate markdown
    lines = [f"# {dir_path.name} Structure", ""]
    
    if format == 'tree':
        # Simple tree format
        for item in structure:
            indent = "|   " * item['depth']
            connector = "|-- " if item['depth'] > 0 else ""
            name = f"{item['name']}/" if item['type'] == 'directory' else item['name']
            lines.append(f"{indent}{connector}{name}")
    else:
        # Bullet list format
        for item in structure:
            indent = "  " * item['depth']
            name = f"{item['name']}/" if item['type'] == 'directory' else item['name']
            lines.append(f"{indent}- {name}")
    
    markdown_content = "\n".join(lines)
    
    if output:
        try:
            with open(output, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            print_success(f"Snapshot saved to: {output}")
        except Exception as e:
            print_error(f"Failed to write output file: {e}")
            return 1
    else:
        click.echo(markdown_content)
    
    return 0

if __name__ == '__main__':
    cli()