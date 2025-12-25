import os
from string import Template
from typing import Dict, Any

class TemplateEngine:
    def __init__(self, templates_dir: str = "templates"):
        self.templates_dir = templates_dir
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, str]:
        """Load template files from templates directory"""
        templates = {}
        if os.path.exists(self.templates_dir):
            for file in os.listdir(self.templates_dir):
                if file.endswith('.j2') or file.endswith('.template'):
                    with open(os.path.join(self.templates_dir, file), 'r') as f:
                        templates[file] = f.read()
        return templates
    
    def render(self, template_name: str, variables: Dict[str, Any] = None) -> str:
        """Render a template with variables"""
        if variables is None:
            variables = {}
        
        # Try to find template in loaded templates
        for key, content in self.templates.items():
            if template_name in key:
                return self._render_string(content, variables)
        
        # Check if template_name is actually a file path
        if os.path.exists(template_name):
            with open(template_name, 'r') as f:
                content = f.read()
                return self._render_string(content, variables)
        
        # If no template found, check for built-in templates
        return self._render_builtin(template_name, variables)
    
    def _render_string(self, template_str: str, variables: Dict[str, Any]) -> str:
        """Render a template string"""
        # Simple template replacement
        for key, value in variables.items():
            placeholder = f'{{{{ {key} }}}}'
            template_str = template_str.replace(placeholder, str(value))
        
        # Also support ${variable} syntax
        try:
            template = Template(template_str)
            return template.substitute(variables)
        except:
            return template_str
    
    def _render_builtin(self, template_type: str, variables: Dict[str, Any]) -> str:
        """Render built-in template types"""
        builtin_templates = {
            'python_module': '''"""
${module_name}
${description}
"""

def main():
    """Main function"""
    print("Hello from ${module_name}!")

if __name__ == "__main__":
    main()
''',
            'python_class': '''class ${class_name}:
    """${description}"""
    
    def __init__(self${init_params}):
        ${init_body}
    
    def __str__(self):
        return "${class_name} instance"
''',
            'readme': '''# ${project_name}

${description}

## Installation
\`\`\`bash
${install_command}
\`\`\`

## Usage
\`\`\`python
${usage_example}
\`\`\`

## License
${license}
''',
            'init': '''"""${module_name} package"""

__version__ = "${version}"
__author__ = "${author}"
'''
        }
        
        template = builtin_templates.get(template_type, '')
        return self._render_string(template, variables)