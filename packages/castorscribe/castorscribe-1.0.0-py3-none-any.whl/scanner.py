import os
import re
from pathlib import Path

def detect_tech_stack(file_path, content):
    """Detect technology stack from file extension and content"""
    tech = set()
    ext = os.path.splitext(file_path)[1].lower()
    
    # File extension detection
    tech_map = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.jsx': 'React',
        '.tsx': 'React',
        '.java': 'Java',
        '.cpp': 'C++',
        '.c': 'C',
        '.cs': 'C#',
        '.go': 'Go',
        '.rs': 'Rust',
        '.php': 'PHP',
        '.rb': 'Ruby',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.html': 'HTML',
        '.css': 'CSS',
        '.scss': 'SASS',
        '.vue': 'Vue.js',
        '.svelte': 'Svelte',
    }
    
    if ext in tech_map:
        tech.add(tech_map[ext])
    
    # Content-based detection
    content_lower = content.lower()
    if 'react' in content_lower or 'import react' in content_lower:
        tech.add('React')
    if 'vue' in content_lower or 'from vue' in content_lower:
        tech.add('Vue.js')
    if 'angular' in content_lower:
        tech.add('Angular')
    if 'express' in content_lower or 'require(\'express\')' in content_lower:
        tech.add('Express.js')
    if 'django' in content_lower or 'from django' in content_lower:
        tech.add('Django')
    if 'flask' in content_lower or 'from flask' in content_lower:
        tech.add('Flask')
    if 'fastapi' in content_lower or 'from fastapi' in content_lower:
        tech.add('FastAPI')
    if 'tensorflow' in content_lower or 'import tensorflow' in content_lower:
        tech.add('TensorFlow')
    if 'pytorch' in content_lower or 'import torch' in content_lower:
        tech.add('PyTorch')
    if 'numpy' in content_lower or 'import numpy' in content_lower:
        tech.add('NumPy')
    if 'pandas' in content_lower or 'import pandas' in content_lower:
        tech.add('Pandas')
    
    return tech

def detect_dependencies(root_path):
    """Detect dependencies from various package manager files"""
    deps = {
        'python': [],
        'node': [],
        'other': []
    }
    
    # Python dependencies
    req_files = ['requirements.txt', 'requirements-dev.txt', 'pyproject.toml', 'setup.py', 'Pipfile']
    for req_file in req_files:
        req_path = os.path.join(root_path, req_file)
        if os.path.exists(req_path):
            try:
                with open(req_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if req_file == 'requirements.txt' or req_file == 'requirements-dev.txt':
                        deps['python'] = [line.strip() for line in content.split('\n') 
                                         if line.strip() and not line.startswith('#')]
                    elif req_file == 'pyproject.toml':
                        # Simple extraction from pyproject.toml
                        matches = re.findall(r'([a-zA-Z0-9_-]+)\s*=', content)
                        deps['python'].extend(matches)
            except:
                pass
    
    # Node.js dependencies
    if os.path.exists(os.path.join(root_path, 'package.json')):
        try:
            import json
            with open(os.path.join(root_path, 'package.json'), 'r', encoding='utf-8') as f:
                pkg = json.load(f)
                if 'dependencies' in pkg:
                    deps['node'].extend(list(pkg['dependencies'].keys()))
                if 'devDependencies' in pkg:
                    deps['node'].extend(list(pkg['devDependencies'].keys()))
        except:
            pass
    
    return deps

def build_file_tree(root_path, max_depth=3, current_depth=0, prefix=""):
    """Build a visual file tree structure"""
    if current_depth >= max_depth:
        return ""
    
    tree_lines = []
    ignore_list = {'.git', 'venv', '__pycache__', '.env', 'node_modules', 
                   '.vscode', '.idea', 'dist', 'build', '.pytest_cache', 
                   'htmlcov', '.coverage', 'target', 'bin', 'obj'}
    
    try:
        items = sorted([item for item in os.listdir(root_path) 
                       if item not in ignore_list and not item.startswith('.')])
        
        for i, item in enumerate(items):
            item_path = os.path.join(root_path, item)
            is_last = i == len(items) - 1
            
            if os.path.isdir(item_path):
                connector = "└── " if is_last else "├── "
                tree_lines.append(f"{prefix}{connector}{item}/")
                
                next_prefix = prefix + ("    " if is_last else "│   ")
                subtree = build_file_tree(item_path, max_depth, current_depth + 1, next_prefix)
                if subtree:
                    tree_lines.append(subtree)
            else:
                connector = "└── " if is_last else "├── "
                tree_lines.append(f"{prefix}{connector}{item}")
    except PermissionError:
        pass
    
    return "\n".join(tree_lines)

def get_project_data(root_path):
    """Comprehensively scan a project and extract all relevant information"""
    abs_path = os.path.abspath(root_path)
    
    project_info = {
        'name': os.path.basename(abs_path).replace('-', ' ').replace('_', ' ').title(),
        'tree': "",
        'file_summaries': [],
        'tech': set(),
        'dependencies': {},
        'main_files': [],
        'has_readme': False,
        'has_license': False,
        'package_manager': None,
        'entry_points': []
    }
    
    ignore_list = {'.git', 'venv', '__pycache__', '.env', 'node_modules', 
                   '.vscode', '.idea', 'dist', 'build', '.pytest_cache', 
                   'htmlcov', '.coverage', 'target', 'bin', 'obj', 'venv'}
    
    # Detect package managers
    if os.path.exists(os.path.join(abs_path, 'package.json')):
        project_info['package_manager'] = 'npm'
    elif os.path.exists(os.path.join(abs_path, 'requirements.txt')):
        project_info['package_manager'] = 'pip'
    elif os.path.exists(os.path.join(abs_path, 'pyproject.toml')):
        project_info['package_manager'] = 'poetry/pip'
    elif os.path.exists(os.path.join(abs_path, 'Pipfile')):
        project_info['package_manager'] = 'pipenv'
    elif os.path.exists(os.path.join(abs_path, 'Cargo.toml')):
        project_info['package_manager'] = 'cargo'
    elif os.path.exists(os.path.join(abs_path, 'go.mod')):
        project_info['package_manager'] = 'go mod'
    
    # Detect dependencies
    project_info['dependencies'] = detect_dependencies(abs_path)
    
    # Build file tree
    project_info['tree'] = build_file_tree(abs_path)
    
    # Scan files
    file_count = 0
    max_files_to_read = 50  # Limit to prevent too much data
    
    for root, dirs, files in os.walk(abs_path):
        # Filter ignored directories
        dirs[:] = [d for d in dirs if d not in ignore_list]
        
        for f in files:
            if f.startswith('.'):
                continue
            
            file_path = os.path.join(root, f)
            rel_path = os.path.relpath(file_path, abs_path)
            
            # Check for special files
            if f.upper() == 'README.MD' or f == 'README.md':
                project_info['has_readme'] = True
                continue
            
            if 'LICENSE' in f.upper():
                project_info['has_license'] = True
                continue
            
            # Detect main/entry files
            if f in ['main.py', 'app.py', 'index.js', 'index.ts', 'main.js', 
                     'app.js', 'server.py', 'run.py', '__main__.py']:
                project_info['entry_points'].append(rel_path)
            
            # Read file content for analysis
            if file_count < max_files_to_read:
                try:
                    # Try to read text files
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                        content = file.read(2000)  # Read first 2000 chars
                        
                        # Detect tech stack
                        detected_tech = detect_tech_stack(file_path, content)
                        project_info['tech'].update(detected_tech)
                        
                        # Store file summary
                        ext = os.path.splitext(f)[1]
                        if ext in ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', 
                                  '.cpp', '.c', '.go', '.rs', '.rb', '.php', '.html', 
                                  '.css', '.vue', '.svelte', '.md', '.json', '.yaml', 
                                  '.yml', '.toml', '.sh', '.bat', '.ps1']:
                            project_info['file_summaries'].append({
                                'path': rel_path,
                                'name': f,
                                'content': content[:1500],  # Limit content size
                                'tech': list(detected_tech)
                            })
                            file_count += 1
                except Exception as e:
                    pass
    
    # Convert tech set to sorted list
    project_info['tech'] = sorted(list(project_info['tech']))
    
    return project_info