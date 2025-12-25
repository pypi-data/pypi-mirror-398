import os
import shutil
from pathlib import Path
from typing import Dict, List
from colorama import Fore, Style, init

init(autoreset=True)

class FileWriter:
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path).resolve()
        self.created_items = []
    
    def create_structure(self, structure: List[Dict], variables: Dict = None) -> List[str]:
        """Create the entire file structure"""
        if variables is None:
            variables = {}
        
        for item in structure:
            self._create_item(item, variables)
        
        return self.created_items
    
    def _create_item(self, item: Dict, variables: Dict):
        """Create a single file or directory"""
        # Replace variables in path and name
        full_path = self._replace_variables(item['full_path'], variables)
        item_path = self.base_path / full_path
        
        if item['type'] == 'directory':
            self._create_directory(item_path, item)
        else:
            self._create_file(item_path, item, variables)
    
    def _create_directory(self, path: Path, item: Dict):
        """Create a directory"""
        try:
            path.mkdir(parents=True, exist_ok=True)
            self.created_items.append(str(path))
            print(f"{Fore.GREEN}✓ Created directory: {path.relative_to(self.base_path)}")
        except Exception as e:
            print(f"{Fore.RED}✗ Failed to create directory {path}: {e}")
    
    def _create_file(self, path: Path, item: Dict, variables: Dict):
        """Create a file with optional content"""
        try:
            # Ensure parent directory exists
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Get file content
            content = self._get_file_content(item, variables)
            
            # Write file
            path.write_text(content, encoding='utf-8')
            self.created_items.append(str(path))
            print(f"{Fore.GREEN}✓ Created file: {path.relative_to(self.base_path)}")
            
        except Exception as e:
            print(f"{Fore.RED}✗ Failed to create file {path}: {e}")
    
    def _get_file_content(self, item: Dict, variables: Dict) -> str:
        """Generate content for a file"""
        # Priority: template > explicit content > empty
        if item.get('template'):
            from mdf.templates import TemplateEngine
            engine = TemplateEngine()
            template_vars = {**variables, **item.get('variables', {})}
            return engine.render(item['template'], template_vars)
        
        elif item.get('content'):
            content = item['content']
            # Replace variables in content
            return self._replace_variables(content, variables)
        
        else:
            # Create empty file or with basic header
            if item['name'].endswith('.py'):
                return f'''# {item['name']}
# Automatically generated
'''
            elif item['name'].endswith('.md'):
                return f'# {item["name"]}\n\n'
            else:
                return ''
    
    def _replace_variables(self, text: str, variables: Dict) -> str:
        """Replace variables in text"""
        for key, value in variables.items():
            placeholder = f'${{{key}}}'
            text = text.replace(placeholder, str(value))
        return text
    
    def cleanup(self):
        """Remove all created files (for testing/rollback)"""
        for item in reversed(self.created_items):
            path = Path(item)
            if path.exists():
                if path.is_file():
                    path.unlink()
                else:
                    shutil.rmtree(path)
                print(f"{Fore.YELLOW}→ Removed: {path.relative_to(self.base_path)}")