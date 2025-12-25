import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import yaml

class MDFParser:
    def __init__(self):
        self.current_depth = 0
        self.path_stack = []
        
    def parse_markdown(self, content: str) -> Dict[str, List]:
        """
        Auto-detect format and parse accordingly
        Returns: {'structure': list of items}
        """
        lines = [line.rstrip() for line in content.strip().split('\n')]
        
        # Check if it's tree syntax (contains tree diagram characters)
        tree_chars = {'│', '├', '└', '─', '┌', '┐'}
        has_tree_chars = any(any(char in line for char in tree_chars) for line in lines)
        
        if has_tree_chars:
            print("🌳 Detected tree diagram format...")
            return self.parse_tree_syntax(content)
        else:
            print("📝 Detected bullet list format...")
            return self.parse_bullet_syntax(content)
    
    def parse_tree_syntax(self, content: str) -> Dict[str, List]:
        """
        Parse tree/diagram syntax with proper Unicode tree characters
        Supports both styles:
        1. project/
           ├── dir1/
           │   ├── file1.py
           │   └── file2.py
           └── dir2/
        
        2. project/
           │
           ├── dir1/
           │   ├── file1.py
           │   └── file2.py
           └── dir2/
        """
        lines = [line.rstrip() for line in content.strip().split('\n')]
        structure = []
        
        # Filter out decorative tree lines (lines that are only tree characters)
        filtered_lines = []
        for line in lines:
            clean = line.replace('│', ' ').replace('├', ' ').replace('└', ' ').replace('─', ' ').replace('┌', ' ').replace('┐', ' ').strip()
            if clean or line.strip() and not line.replace(' ', '').replace('│', '').replace('├', '').replace('└', '').replace('─', '').replace('┌', '').replace('┐', ''):
                filtered_lines.append(line)
        
        lines = filtered_lines
        
        for line in lines:
            # Skip empty lines
            if not line:
                continue
            
            # Remove trailing comments
            line_without_comments = line.split('#')[0].rstrip()
            if not line_without_comments:
                continue
            
            # Calculate depth based on tree characters
            # Count leading spaces + tree characters as indentation
            original_line = line
            
            # Convert tree characters to a consistent format
            line = line.replace('├── ', '│   ').replace('└── ', '│   ').replace('│   ', '│   ')
            
            # Count indentation: each '│   ' is 4 spaces, each 4 spaces is one level
            indent_count = 0
            i = 0
            while i < len(line):
                if line.startswith('│   ', i):
                    indent_count += 1
                    i += 4
                elif line.startswith('    ', i):
                    indent_count += 1
                    i += 4
                elif line[i] == ' ':
                    i += 1
                else:
                    break
            
            depth = indent_count
            
            # Extract the actual item name
            # Remove tree characters from the beginning
            item_line = line.lstrip()
            item_line = re.sub(r'^[│├└─┌┐\s]+', '', item_line)
            
            # Extract filename and optional comment
            parts = item_line.split('#', 1)
            item_name = parts[0].strip()
            
            if not item_name:
                continue
            
            # Parse item details
            item = self._parse_line(item_line)
            item['depth'] = depth
            
            # Build full path based on depth
            if depth == 0:
                self.path_stack = [item['name']]
                full_path = item['name']
            else:
                # Ensure path stack has correct depth
                while len(self.path_stack) > depth:
                    self.path_stack.pop()
                
                if depth > len(self.path_stack):
                    # If we're going deeper, use last directory as parent
                    self.path_stack.append(self.path_stack[-1] if self.path_stack else '')
                
                # Update current level in stack
                if depth <= len(self.path_stack):
                    self.path_stack = self.path_stack[:depth]
                
                # Add current item to path
                parent_path = '/'.join(self.path_stack) if self.path_stack else ''
                full_path = f"{parent_path}/{item['name']}" if parent_path else item['name']
                
                # If it's a directory, add to path stack for next items
                if item['type'] == 'directory':
                    if depth >= len(self.path_stack):
                        self.path_stack.append(item['name'])
                    else:
                        self.path_stack[depth] = item['name']
            
            item['full_path'] = full_path
            structure.append(item)
        
        return {'structure': structure}
    
    def parse_bullet_syntax(self, content: str) -> Dict[str, List]:
        """
        Parse traditional bullet list syntax
        Format:
        - project/
          - src/
            - main.py
        """
        lines = content.strip().split('\n')
        structure = []
        self.current_depth = 0
        self.path_stack = []
        
        for line in lines:
            line = line.rstrip()
            if line.strip() == '' or line.strip().startswith('#'):
                continue
                
            # Count indentation (spaces)
            indent = len(line) - len(line.lstrip())
            depth = indent // 2  # Assuming 2 spaces per level
            
            # Clean the line
            clean_line = line.strip()
            
            # Remove list markers
            if clean_line.startswith('- '):
                clean_line = clean_line[2:]
            elif clean_line.startswith('* '):
                clean_line = clean_line[2:]
            elif clean_line.startswith('+ '):
                clean_line = clean_line[2:]
            
            # Parse the line
            item = self._parse_line(clean_line)
            item['depth'] = depth
            
            # Update path stack based on depth
            if depth <= self.current_depth:
                self.path_stack = self.path_stack[:depth]
            
            # Build full path
            if self.path_stack:
                full_path = '/'.join(self.path_stack + [item['name']])
            else:
                full_path = item['name']
            
            item['full_path'] = full_path
            
            # Add to structure
            structure.append(item)
            
            # If it's a directory, add to path stack for next items
            if item['type'] == 'directory':
                if depth >= len(self.path_stack):
                    self.path_stack.append(item['name'])
                else:
                    self.path_stack[depth] = item['name']
                self.current_depth = depth
        
        return {'structure': structure}
    
    def _parse_line(self, line: str) -> Dict:
        """Parse a single line to extract file/directory info"""
        item = {
            'name': '',
            'type': 'file',
            'content': '',
            'template': None,
            'variables': {},
            'comment': ''
        }
        
        # Extract comment if present
        if '#' in line:
            main_part, comment_part = line.split('#', 1)
            item['comment'] = comment_part.strip()
            line = main_part.strip()
        else:
            line = line.strip()
        
        if not line:
            return item
        
        # Check if it's a directory (ends with / in tree diagrams)
        if line.endswith('/'):
            item['type'] = 'directory'
            item['name'] = line[:-1].strip()
        else:
            item['name'] = line.strip()
            
            # Check for template/content in comment
            if item['comment']:
                comment = item['comment']
                if comment.startswith('template:'):
                    item['template'] = comment.split(':', 1)[1].strip()
                elif comment.startswith('content:'):
                    item['content'] = comment.split(':', 1)[1].strip()
                elif comment.startswith('vars:'):
                    var_str = comment.split(':', 1)[1].strip()
                    # Parse variables like "name:value,type:module"
                    for pair in var_str.split(','):
                        if ':' in pair:
                            key, value = pair.split(':', 1)
                            item['variables'][key.strip()] = value.strip()
        
        return item
    
    def parse_yaml_frontmatter(self, content: str) -> Tuple[Dict, str]:
        """Parse YAML frontmatter if present"""
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                yaml_content = parts[1]
                markdown_content = parts[2]
                try:
                    config = yaml.safe_load(yaml_content) or {}
                    return config, markdown_content
                except yaml.YAMLError:
                    return {}, content
        return {}, content
    
    def detect_format(self, content: str) -> str:
        """Detect the format of the markdown content"""
        lines = content.strip().split('\n')[:10]  # Check first 10 lines
        
        tree_chars = {'│', '├', '└', '─', '┌', '┐'}
        bullet_chars = {'-', '*', '+'}
        
        for line in lines:
            line = line.strip()
            if any(char in line for char in tree_chars):
                return 'tree'
            elif line and line[0] in bullet_chars:
                return 'bullet'
        
        return 'unknown'