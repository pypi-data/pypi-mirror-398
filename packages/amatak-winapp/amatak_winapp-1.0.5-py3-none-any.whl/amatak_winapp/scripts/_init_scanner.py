# C:\Users\USER\OneDrive\Desktop\developer\OpenSource\pip-package\winapp\amatak_winapp\scripts\_init_scanner.py

import os
import sys
from datetime import datetime
from pathlib import Path

# Add package directory to path to import from amatak_winapp
script_dir = Path(__file__).parent
package_root = script_dir.parent
sys.path.insert(0, str(package_root))

# Configuration
EXCLUDE_DIRS = {".venv", ".git", "__pycache__", ".idea", ".vscode", "installer", "assets"}
CURRENT_YEAR = datetime.now().year
OWNER = "Amatak Holdings Pty Ltd"

def get_package_version():
    """Reads version from amatak_winapp/data/VERSION.txt or returns default."""
    # First try to read directly from the data directory
    version_file = package_root / "data" / "VERSION.txt"
    if version_file.exists():
        try:
            version = version_file.read_text(encoding='utf-8').strip()
            print(f"[INFO] Found package version in data/VERSION.txt: {version}")
            return version
        except Exception as e:
            print(f"[WARNING] Could not read version from {version_file}: {e}")
    
    # Try to import from package
    try:
        from amatak_winapp import __version__
        print(f"[INFO] Using __version__ from package: {__version__}")
        return __version__
    except ImportError as e:
        print(f"[WARNING] Could not import __version__: {e}")
    
    # Final fallback
    return "1.0.2"

def get_project_version():
    """Reads version from project's VERSION.txt (if exists) or uses package version."""
    # First check for project-specific VERSION.txt
    project_version_file = Path.cwd() / "VERSION.txt"
    if project_version_file.exists():
        try:
            version = project_version_file.read_text(encoding='utf-8').strip()
            print(f"[INFO] Using project version from VERSION.txt: {version}")
            return version
        except Exception as e:
            print(f"[WARNING] Could not read project VERSION.txt: {e}")
    
    # Use package version as fallback
    return get_package_version()

def generate_inits():
    """Scans subdirectories and ensures they are valid Python packages with versioning."""
    project_root = os.getcwd()
    current_version = get_project_version()
    
    print(f"\n[SCANNER] Starting initialization with version: {current_version}")
    print("=" * 60)
    
    # Updated Header with Version
    copyright_header = (
        f'"""\n'
        f'Auto-generated package initialization.\n'
        f'Copyright (c) {CURRENT_YEAR} {OWNER}.\n'
        f'"""\n\n'
    )

    init_count = 0
    
    for root, dirs, files in os.walk(project_root):
        # Filter excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        # Skip project root (we'll handle it separately)
        if root == project_root:
            continue

        init_path = os.path.join(root, "__init__.py")
        
        # Find all .py modules (excluding __init__ and scripts)
        py_modules = sorted([
            f[:-3] for f in files 
            if f.endswith(".py") and f not in ["__init__.py", "_init_scanner.py"]
        ])

        # Generate the content components
        version_line = f'__version__ = "{current_version}"\n'
        
        # Build import lines
        import_lines = []
        if py_modules:
            import_lines = [f"from . import {module}" for module in py_modules]
        
        # Add modules + version variable to __all__
        export_list = py_modules + ["__version__"]
        all_line = f"__all__ = {export_list}"
        
        # Assemble file content
        full_content = copyright_header
        full_content += version_line
        if import_lines:
            full_content += "\n".join(import_lines) + "\n\n"
        full_content += all_line + "\n"

        # Write the file
        try:
            with open(init_path, "w", encoding="utf-8") as f:
                f.write(full_content)
            
            rel_folder = os.path.relpath(root, project_root)
            print(f"[OK] [{CURRENT_YEAR}] Initialized: {rel_folder}/__init__.py (v{current_version})")
            init_count += 1
        except Exception as e:
            rel_folder = os.path.relpath(root, project_root)
            print(f"[ERROR] Failed to initialize {rel_folder}/__init__.py: {e}")
    
    # Special handling for the package root __init__.py
    if str(project_root).endswith("amatak_winapp"):
        package_init_path = os.path.join(project_root, "__init__.py")
        try:
            # Read current __init__.py to preserve other content
            current_content = ""
            if os.path.exists(package_init_path):
                with open(package_init_path, "r", encoding="utf-8") as f:
                    current_content = f.read()
            
            # Find and replace version line if it exists
            if "__version__ = " in current_content:
                lines = current_content.split('\n')
                new_lines = []
                for line in lines:
                    if line.strip().startswith('__version__ = '):
                        new_lines.append(f'__version__ = "{current_version}"')
                    else:
                        new_lines.append(line)
                new_content = '\n'.join(new_lines)
            else:
                # Add version line at the top
                new_content = f'__version__ = "{current_version}"\n\n' + current_content
            
            # Write updated content
            with open(package_init_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            
            print(f"\n[INFO] Updated package __init__.py with version: {current_version}")
        except Exception as e:
            print(f"[WARNING] Could not update package __init__.py: {e}")
    
    print("=" * 60)
    print(f"[SUCCESS] Initialization complete! Created/updated {init_count} __init__.py files")
    print(f"[INFO] Package version: {current_version}")

if __name__ == "__main__":
    print("AMATAK INIT SCANNER - Generating/Updating __init__.py files")
    print("=" * 60)
    generate_inits()