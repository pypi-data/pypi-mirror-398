import os
from datetime import datetime

# Configuration
TREE_FILE = "tree.txt"
README_FILE = "README.md"
CURRENT_YEAR = datetime.now().year
PROJECT_NAME = os.path.basename(os.getcwd())

def get_folders_from_tree(file_path):
    """Parses folder names from the formatted tree.txt file."""
    folders = []
    if not os.path.exists(file_path):
        return folders
        
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    for line in lines:
        # Looking for lines ending in '/' or directory indicators in the visual tree
        clean_line = line.strip().replace("├── ", "").replace("└── ", "").replace("│   ", "")
        if clean_line.endswith("/") or "/" in line:
            folder_name = clean_line.replace("/", "").strip()
            if folder_name and folder_name != PROJECT_NAME:
                folders.append(folder_name)
    return sorted(list(set(folders)))

def generate_readme():
    """Generates a standard README.md based on tree structure."""
    folders = get_folders_from_tree(TREE_FILE)
    
    # 1. Top Copyright Header
    content = f"Copyright (c) {CURRENT_YEAR} Amatak Holdings Pty Ltd.\n\n"
    
    # 2. Main Title & Introduction
    content += f"# {PROJECT_NAME}\n\n"
    content += "This project is an automated AI utility suite. This README is auto-generated based on the project structure.\n\n"
    
    # 3. Project Structure Section
    content += "## Project Structure\n"
    if os.path.exists(TREE_FILE):
        with open(TREE_FILE, "r", encoding="utf-8") as f:
            tree_content = f.read()
        content += f"{tree_content}\n"
    
    # 4. Folder Specific Explanations
    content += "## Documentation & Modules\n"
    for folder in folders:
        content += f"### {folder}/\n"
        content += f"Standard module for `{folder}` functionality. Contains core logic and package initializations.\n\n"
        
    # 5. Generic Setup Instructions
    content += "## Setup\n"
    content += "```bash\npip install -r requirements.txt\npython main.py\n```\n"

    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"[{CURRENT_YEAR}] README.md successfully updated from {TREE_FILE}.")

if __name__ == "__main__":
    generate_readme()