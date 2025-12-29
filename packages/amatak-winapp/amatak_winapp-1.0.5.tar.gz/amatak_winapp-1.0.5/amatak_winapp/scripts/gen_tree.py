import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configuration
MONITOR_PATH = os.getcwd()
OUTPUT_FILE = "tree.txt"
EXCLUDE_DIRS = {".venv","gen_tree.py","gen_nsi.py","use","gen_license_agreement.py", "gen_brand.py","gen_license.py" ,"gen_update.py",".git", "__pycache__", ".idea", ".vscode"}

def generate_visual_tree(path, prefix=""):
    """Recursively builds a tree string with branching characters."""
    items = sorted([
        item for item in os.listdir(path) 
        if item not in EXCLUDE_DIRS and item != OUTPUT_FILE
    ])
    
    tree_str = ""
    count = len(items)
    for i, item in enumerate(items):
        is_last = (i == count - 1)
        full_path = os.path.join(path, item)
        connector = "└── " if is_last else "├── "
        tree_str += f"{prefix}{connector}{item}\n"
        
        if os.path.isdir(full_path):
            extension = "    " if is_last else "│   "
            tree_str += generate_visual_tree(full_path, prefix + extension)
    return tree_str

def write_tree():
    """Generates the tree and wraps it in triple backticks for Markdown compatibility."""
    root_name = os.path.basename(MONITOR_PATH) or "Project_Root"
    
    # Building the content with backticks at top and bottom
    tree_content = generate_visual_tree(MONITOR_PATH)
    full_output = f"```\n{root_name}/\n{tree_content}```"
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(full_output)
    print(f"[{time.strftime('%H:%M:%S')}] tree.txt updated with code block formatting.")

class UpdateTreeHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        # Ignore changes to the output file or excluded folders to prevent loops
        path_parts = event.src_path.split(os.sep)
        if any(ex in path_parts for ex in EXCLUDE_DIRS) or event.src_path.endswith(OUTPUT_FILE):
            return
        
        if not event.is_directory:
            write_tree()

if __name__ == "__main__":
    write_tree()
    
    event_handler = UpdateTreeHandler()
    observer = Observer()
    observer.schedule(event_handler, MONITOR_PATH, recursive=True)
    
    print(f"Monitoring: {MONITOR_PATH}")
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()