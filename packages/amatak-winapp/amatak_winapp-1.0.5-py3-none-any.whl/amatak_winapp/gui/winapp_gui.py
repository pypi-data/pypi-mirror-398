# C:\Users\USER\OneDrive\Desktop\developer\OpenSource\pip-package\winapp\amatak_winapp\gui\winapp_gui.py

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import sys
import subprocess
import json
import shutil
from pathlib import Path
import threading
import webbrowser
import datetime

# Add package directory to path
PACKAGE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PACKAGE_DIR))

# Import ProjectGenerator
try:
    from winapp import ProjectGenerator
except ImportError:
    # Try absolute import
    from amatak_winapp.winapp import ProjectGenerator

def get_version():
    """Get version from data/VERSION.txt"""
    version_file = PACKAGE_DIR / "data" / "VERSION.txt"
    if version_file.exists():
        try:
            return version_file.read_text(encoding='utf-8').strip()
        except:
            return "1.0.0"
    return "1.0.0"

class WinAppGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Amatak WinApp Generator v{get_version()}")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # Set icon
        self.set_icon()

        # Center window
        self.center_window()
        
        # Setup styles
        self.setup_styles()
        
        # Setup variables
        self.project_generator = ProjectGenerator()
        self.current_project_path = Path.cwd()
        
        # Build UI
        self.create_menu()
        self.create_main_frame()
        
        # Bind window events
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def set_icon(self):
        """Set window icon"""
        try:
            icon_path = PACKAGE_DIR / "assets" / "brand" / "brand.ico"
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
        except:
            pass
    
    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def setup_styles(self):
        """Setup ttk styles"""
        style = ttk.Style()
        
        # Configure styles
        style.configure('Title.TLabel', font=('Segoe UI', 16, 'bold'))
        style.configure('Heading.TLabel', font=('Segoe UI', 12, 'bold'))
        style.configure('Success.TLabel', foreground='green')
        style.configure('Error.TLabel', foreground='red')
        
        # Configure button styles
        style.configure('Accent.TButton', font=('Segoe UI', 10, 'bold'))
        style.configure('Large.TButton', font=('Segoe UI', 11), padding=10)
    
    def create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Project...", command=self.create_project)
        file_menu.add_command(label="Open Project...", command=self.browse_project)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Initialize Project", command=self.show_initialize_tab)
        tools_menu.add_command(label="Build Installer", command=self.build_project)
        tools_menu.add_separator()
        tools_menu.add_command(label="Open Project Folder", command=self.open_project_folder)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self.open_docs)
        help_menu.add_command(label="About", command=self.show_about)
    
    def create_main_frame(self):
        """Create main frame with notebook"""
        # Header
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(header_frame, 
                 text="🎯 Amatak WinApp Generator",
                 style='Title.TLabel').pack(side=tk.LEFT)
        
        ttk.Label(header_frame,
                 text=f"v{get_version()}",
                 foreground="#666666",
                 font=("Segoe UI", 10)).pack(side=tk.RIGHT)
        
        # Current project info
        info_frame = ttk.LabelFrame(self.root, text="Current Project", padding=10)
        info_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        self.project_label = ttk.Label(info_frame, 
                                      text=f"📁 {self.current_project_path}",
                                      font=("Segoe UI", 10))
        self.project_label.pack(fill=tk.X)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Create tabs
        self.create_welcome_tab()
        self.create_initialize_tab()
        self.create_build_tab()
        self.create_logs_tab()

        
    
    def create_welcome_tab(self):
        """Create welcome/home tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🏠 Home")
        
        # Welcome content
        content_frame = ttk.Frame(tab)
        content_frame.pack(expand=True, fill=tk.BOTH, padx=40, pady=40)
        
        # Welcome message
        welcome_text = f"""Welcome to Amatak WinApp v{get_version()}!

A comprehensive toolkit for creating Windows application installers.

🚀 Quick Start:
1. Create a new project or select existing one
2. Initialize project (branding, docs, etc.)
3. Build the Windows installer

📋 Features:
• Create complete Windows application projects
• Generate professional branding assets
• Build NSIS-based installers
• Easy-to-use graphical interface
• Command-line support

Select a tab above to get started!
"""
        
        text_widget = scrolledtext.ScrolledText(content_frame, 
                                               wrap=tk.WORD,
                                               font=("Segoe UI", 11),
                                               height=15,
                                               padx=20,
                                               pady=20)
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert("1.0", welcome_text)
        text_widget.config(state=tk.DISABLED)
        
        # Quick action buttons
        button_frame = ttk.Frame(tab)
        button_frame.pack(fill=tk.X, padx=40, pady=(0, 30))
        
        ttk.Button(button_frame, 
                  text="🚀 Create New Project",
                  style='Large.TButton',
                  command=self.create_project).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame,
                  text="📁 Select Project",
                  style='Large.TButton',
                  command=self.browse_project).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame,
                  text="⚡ Quick Initialize",
                  style='Large.TButton',
                  command=self.quick_initialize).pack(side=tk.RIGHT, padx=5)
        


    def initialize_gen_nsi(self, project_path):
        """Initialize/Generate NSIS installer script"""
        self.log_message("📝 Initializing/Generating NSIS installer script...")
        
        # Check if gen_nsi.py exists in scripts directory
        scripts_dir = Path(__file__).parent.parent / "scripts"
        gen_nsi_script = scripts_dir / "gen_nsi.py"
        
        if not gen_nsi_script.exists():
            self.log_message("❌ gen_nsi.py not found in scripts directory", "ERROR")
            return False
        
        try:
            # Run gen_nsi.py
            import subprocess
            result = subprocess.run(
                [sys.executable, str(gen_nsi_script)],
                cwd=str(project_path),
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            if result.returncode == 0:
                self.log_message("✅ NSIS installer script generated successfully!", "SUCCESS")
                self.log_message(f"Output: {result.stdout}")
                
                # Check if the NSIS file was created
                nsi_file = project_path / "installer" / "win_installer.nsi"
                if nsi_file.exists():
                    self.log_message(f"📁 NSIS script created: {nsi_file}")
                else:
                    self.log_message(f"⚠️ NSIS script may not have been created", "WARNING")
                
                return True
            else:
                self.log_message(f"❌ Failed to generate NSIS script", "ERROR")
                if result.stderr:
                    self.log_message(f"Error: {result.stderr[:500]}")
                return False
                
        except Exception as e:
            self.log_message(f"❌ Exception while running gen_nsi.py: {e}", "ERROR")
            return False

    def initialize_gen_win(self, project_path):
        """Initialize/Generate Windows build files"""
        self.log_message("🪟 Initializing/Generating Windows build files...")
        
        # Check if gen_win.py exists in scripts directory
        scripts_dir = Path(__file__).parent.parent / "scripts"
        gen_win_script = scripts_dir / "gen_win.py"
        
        if not gen_win_script.exists():
            self.log_message("❌ gen_win.py not found in scripts directory", "ERROR")
            return False
        
        try:
            # Run gen_win.py
            import subprocess
            result = subprocess.run(
                [sys.executable, str(gen_win_script)],
                cwd=str(project_path),
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            if result.returncode == 0:
                self.log_message("✅ Windows build files generated successfully!", "SUCCESS")
                self.log_message(f"Output: {result.stdout}")
                return True
            else:
                self.log_message(f"❌ Failed to generate Windows build files", "ERROR")
                if result.stderr:
                    self.log_message(f"Error: {result.stderr[:500]}")
                return False
                
        except Exception as e:
            self.log_message(f"❌ Exception while running gen_win.py: {e}", "ERROR")
            return False

    def initialize_script(self, script_name, project_path):
        """Initialize a specific script"""
        if script_name == "gen_brand.py":
            return self.initialize_gen_brand(project_path)
        elif script_name == "gen_nsi.py":
            return self.initialize_gen_nsi(project_path)
        elif script_name == "gen_win.py":
            return self.initialize_gen_win(project_path)
        elif script_name == "winapp_init.py":
            return self.run_winapp_init(project_path)
        elif script_name == "_init_scanner.py":
            return self.run_init_scanner(project_path)
        elif script_name == "gen_readme.py":
            return self.run_gen_readme(project_path)
        elif script_name == "gen_license.py":
            return self.run_gen_license(project_path)
        else:
            self.log_message(f"⚠️ Unknown script: {script_name}", "WARNING")
            return False

    def run_init_scanner(self, project_path):
        """Run _init_scanner.py"""
        self.log_message("🔍 Running project structure scanner...")
        
        scripts_dir = Path(__file__).parent.parent / "scripts"
        init_scanner_script = scripts_dir / "_init_scanner.py"
        
        if not init_scanner_script.exists():
            self.log_message("❌ _init_scanner.py not found", "ERROR")
            return False
        
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, str(init_scanner_script)],
                cwd=str(project_path),
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            if result.returncode == 0:
                self.log_message("✅ Project structure scanner completed!", "SUCCESS")
                self.log_message(f"Output: {result.stdout}")
                return True
            else:
                self.log_message(f"❌ Project structure scanner failed", "ERROR")
                if result.stderr:
                    self.log_message(f"Error: {result.stderr[:500]}")
                return False
                
        except Exception as e:
            self.log_message(f"❌ Exception while running _init_scanner.py: {e}", "ERROR")
            return False

    def run_gen_readme(self, project_path):
        """Run gen_readme.py"""
        self.log_message("📝 Generating README documentation...")
        
        scripts_dir = Path(__file__).parent.parent / "scripts"
        gen_readme_script = scripts_dir / "gen_readme.py"
        
        if not gen_readme_script.exists():
            self.log_message("❌ gen_readme.py not found", "ERROR")
            return False
        
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, str(gen_readme_script)],
                cwd=str(project_path),
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            if result.returncode == 0:
                self.log_message("✅ README documentation generated!", "SUCCESS")
                self.log_message(f"Output: {result.stdout}")
                
                # Check if README was created
                readme_file = project_path / "README.md"
                if readme_file.exists():
                    self.log_message(f"📁 README created: {readme_file}")
                else:
                    self.log_message(f"⚠️ README may not have been created", "WARNING")
                
                return True
            else:
                self.log_message(f"❌ Failed to generate README", "ERROR")
                if result.stderr:
                    self.log_message(f"Error: {result.stderr[:500]}")
                return False
                
        except Exception as e:
            self.log_message(f"❌ Exception while running gen_readme.py: {e}", "ERROR")
            return False
        

    def run_gen_license(self, project_path):
        """Generate MIT License file (simple version)"""
        self.log_message("📜 Generating MIT License file...")
        
        # Get current year
        currentyear = datetime.datetime.now().year
        
        # Use directory name as app name
        currentapp = project_path.name
        
        # MIT License template
        license_content = f"""MIT License

    Copyright (c) {currentyear} {currentapp}

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE."""
        
        try:
            # Write LICENSE file
            license_file = project_path / "LICENSE"
            license_file.write_text(license_content, encoding='utf-8')
            
            self.log_message(f"✅ MIT License file generated: {license_file}")
            return True
            
        except Exception as e:
            self.log_message(f"❌ Failed to generate LICENSE file: {e}", "ERROR")
            return False

    def run_winapp_init(self, project_path):
        """Run winapp_init.py"""
        self.log_message("🚀 Running main project initialization...")
        
        scripts_dir = Path(__file__).parent.parent / "scripts"
        winapp_init_script = scripts_dir / "winapp_init.py"
        
        if not winapp_init_script.exists():
            self.log_message("❌ winapp_init.py not found", "ERROR")
            return False
        
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, str(winapp_init_script)],
                cwd=str(project_path),
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            if result.returncode == 0:
                self.log_message("✅ Project initialization completed!", "SUCCESS")
                self.log_message(f"Output: {result.stdout}")
                return True
            else:
                self.log_message(f"❌ Project initialization failed", "ERROR")
                if result.stderr:
                    self.log_message(f"Error: {result.stderr[:500]}")
                return False
                
        except Exception as e:
            self.log_message(f"❌ Exception while running winapp_init.py: {e}", "ERROR")
            return False

    def update_run_initialization_thread(self, project_path, scripts):
        """Updated thread function for running initialization"""
        self.log_message(f"Starting initialization for: {project_path}")
        
        success_count = 0
        total_scripts = len(scripts)
        
        for i, script in enumerate(scripts, 1):
            self.log_message(f"Running {script} ({i}/{total_scripts})...")
            
            try:
                success = self.initialize_script(script, project_path)
                
                if success:
                    self.log_message(f"{script} completed successfully", "SUCCESS")
                    success_count += 1
                else:
                    self.log_message(f"{script} failed", "ERROR")
                    
            except Exception as e:
                self.log_message(f"Error running {script}: {e}", "ERROR")
        
        # Summary
        if success_count == total_scripts:
            self.log_message(f"✅ All {success_count} scripts completed successfully!", "SUCCESS")
            messagebox.showinfo("Success", 
                            f"Initialization completed successfully!\n" +
                            f"{success_count}/{total_scripts} scripts executed.")
        else:
            self.log_message(f"⚠️  {success_count}/{total_scripts} scripts completed", "WARNING")
            messagebox.showwarning("Partial Success",
                                f"Initialization partially completed.\n" +
                                f"{success_count}/{total_scripts} scripts executed.")
    
    def create_initialize_tab(self):
        """Create project initialization tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="⚙️ Initialize")
        
        # Instructions
        instructions = ttk.LabelFrame(tab, text="Instructions", padding=15)
        instructions.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(instructions,
                text="This will run initialization scripts to set up your project.\n" +
                    "Select the scripts you want to run and click 'Initialize'.",
                font=("Segoe UI", 10)).pack(anchor=tk.W)
        
        # Project selection
        project_frame = ttk.LabelFrame(tab, text="Project Settings", padding=15)
        project_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(project_frame, 
                text="Project Path:",
                font=("Segoe UI", 10, "bold")).grid(row=0, column=0, 
                                                    sticky=tk.W, pady=5)
        
        path_frame = ttk.Frame(project_frame)
        path_frame.grid(row=0, column=1, sticky=tk.W+tk.E, 
                    pady=5, padx=(10, 0), columnspan=2)
        
        self.init_path_var = tk.StringVar(value=str(self.current_project_path))
        self.init_path_entry = ttk.Entry(path_frame, 
                                        textvariable=self.init_path_var,
                                        width=50,
                                        font=("Segoe UI", 10))
        self.init_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(path_frame, 
                text="Browse",
                command=self.browse_init_project,
                width=10).pack(side=tk.RIGHT, padx=(10, 0))
        
        # Quick action buttons
        quick_actions_frame = ttk.LabelFrame(tab, text="Quick Actions", padding=15)
        quick_actions_frame.pack(fill=tk.X, padx=10, pady=10)
        
        quick_buttons_frame = ttk.Frame(quick_actions_frame)
        quick_buttons_frame.pack(fill=tk.X)
        
        # Add dedicated branding button
        ttk.Button(quick_buttons_frame,
                text="🎨 Generate Branding",
                command=self.generate_branding_only,
                width=20).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(quick_buttons_frame,
                text="📝 Generate README",
                command=self.generate_readme_only,
                width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(quick_buttons_frame,
                text="📝 Generate License",
                command=self.generate_license_only,
                width=20).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(quick_buttons_frame,
                text="📦 Generate NSI",
                command=self.generate_nsi_only,
                width=20).pack(side=tk.LEFT, padx=5)
        
        # Scripts selection
        scripts_frame = ttk.LabelFrame(tab, text="Available Scripts", padding=15)
        scripts_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create a canvas with scrollbar for scripts
        canvas_frame = ttk.Frame(scripts_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(canvas_frame)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Define available scripts
        self.scripts_vars = {}
        scripts = [
            ("winapp_init.py", "Main project initialization", "🚀", True),
            ("_init_scanner.py", "Scan and validate project structure", "🔍", True),
            ("gen_readme.py", "Generate README documentation", "📝", True),
            ("gen_brand.py", "Generate branding assets", "🎨", True),
            ("gen_nsi.py", "Generate NSIS installer script", "📦", True),
            ("gen_license.py", "Generate License script", "📦", True),
            ("gen_win.py", "Generate Windows build files", "🪟", True),
        ]
        
        for i, (script, description, icon, enabled) in enumerate(scripts):
            var = tk.BooleanVar(value=enabled)
            self.scripts_vars[script] = var
            
            # Script frame
            script_frame = ttk.Frame(scrollable_frame)
            script_frame.pack(fill=tk.X, padx=5, pady=3)
            
            # Checkbox
            cb = ttk.Checkbutton(script_frame,
                                text=f"  {icon} {script}",
                                variable=var,
                                state=tk.NORMAL)
            cb.pack(side=tk.LEFT, anchor=tk.W)
            
            # Description
            ttk.Label(script_frame,
                    text=description,
                    font=("Segoe UI", 9),
                    foreground="#666666").pack(side=tk.LEFT, padx=(20, 0))
        
        # Control buttons
        control_frame = ttk.Frame(tab)
        control_frame.pack(fill=tk.X, padx=10, pady=20)
        
        # Select all/none buttons
        select_frame = ttk.Frame(control_frame)
        select_frame.pack(side=tk.LEFT)
        
        ttk.Button(select_frame,
                text="✓ Select All",
                command=self.select_all_scripts).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(select_frame,
                text="✗ Clear All",
                command=self.clear_all_scripts).pack(side=tk.LEFT, padx=2)
        
        # Main action buttons
        action_frame = ttk.Frame(control_frame)
        action_frame.pack(side=tk.RIGHT)
        
        ttk.Button(action_frame,
                text="🔄 Initialize",
                style='Accent.TButton',
                command=self.run_initialization).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(action_frame,
                text="📁 Update Tree",
                command=self.update_tree).pack(side=tk.RIGHT, padx=5)
        



    def generate_branding_only_for_build_tab(self):
        """Generate branding from build tab"""
        project_path = Path(self.build_path_var.get())
        
        if not project_path.exists():
            messagebox.showerror("Error", f"Project path does not exist:\n{project_path}")
            return
        
        # Run in background thread
        thread = threading.Thread(
            target=self._generate_branding_thread,
            args=(project_path,),
            daemon=True
        )
        thread.start()

    def check_branding_assets(self):
        """Check if branding assets exist"""
        project_path = Path(self.build_path_var.get())
        
        if not project_path.exists():
            messagebox.showerror("Error", f"Project path does not exist:\n{project_path}")
            return
        
        brand_dir = project_path / "assets" / "brand"
        
        if not brand_dir.exists():
            self.log_message(f"Branding directory not found: {brand_dir}", "WARNING")
            response = messagebox.askyesno("Missing Branding", 
                                        "Branding assets directory not found.\n"
                                        "Would you like to generate branding assets now?")
            if response:
                self.generate_branding_only_for_build_tab()
            return
        
        # Check for essential branding files
        essential_files = [
            ("brand.ico", "Application icon (ICO format)"),
            ("brand.png", "Application icon (PNG format)"),
            ("brand_installer.bmp", "Installer banner (BMP format, 150x57 pixels)"),
        ]
        
        missing_files = []
        for filename, description in essential_files:
            file_path = brand_dir / filename
            if not file_path.exists():
                missing_files.append((filename, description))
        
        if missing_files:
            self.log_message(f"Missing {len(missing_files)} essential branding files:", "WARNING")
            for filename, description in missing_files:
                self.log_message(f"  - {filename}: {description}", "WARNING")
            
            message = f"Missing {len(missing_files)} essential branding files:\n\n"
            for filename, description in missing_files:
                message += f"• {filename}: {description}\n"
            message += "\nSome features may not work correctly."
            
            response = messagebox.askyesno("Missing Branding Files", 
                                        message + "\n\nWould you like to generate branding assets now?")
            if response:
                self.generate_branding_only_for_build_tab()
        else:
            self.log_message("All essential branding files found!", "SUCCESS")
            messagebox.showinfo("Branding Check", "All essential branding files are present!")
        

    def generate_branding_only(self):
        """Generate only branding assets"""
        project_path = Path(self.init_path_var.get())
        
        if not project_path.exists():
            messagebox.showerror("Error", f"Project path does not exist:\n{project_path}")
            return
        
        # Run in background thread
        thread = threading.Thread(
            target=self._generate_branding_thread,
            args=(project_path,),
            daemon=True
        )
        thread.start()

    def _generate_branding_thread(self, project_path):
        """Thread function for generating branding assets"""
        self.log_message(f"Generating branding assets for: {project_path}")
        
        # Update generator with project path
        self.project_generator = ProjectGenerator(project_path)
        
        success = self.initialize_gen_brand(project_path)
        
        if success:
            self.log_message("Branding assets generated successfully!", "SUCCESS")
            messagebox.showinfo("Success", "Branding assets generated successfully!")
        else:
            self.log_message("Failed to generate branding assets!", "ERROR")
            messagebox.showerror("Error", "Failed to generate branding assets!")

    def generate_readme_only(self):
        """Generate only README documentation"""
        project_path = Path(self.init_path_var.get())
        
        if not project_path.exists():
            messagebox.showerror("Error", f"Project path does not exist:\n{project_path}")
            return
        
        # Run in background thread
        thread = threading.Thread(
            target=self._generate_readme_thread,
            args=(project_path,),
            daemon=True
        )
        thread.start()


    def generate_license_only(self):
        """Generate only License"""
        project_path = Path(self.init_path_var.get())
        
        # Validate project path
        if not project_path.exists():
            messagebox.showerror("Error", f"Project path does not exist:\n{project_path}")
            return
        
        # Check if it's a valid project directory
        if not (project_path / "main.py").exists() and not (project_path / "config.json").exists():
            response = messagebox.askyesno(
                "Warning", 
                f"This doesn't look like a project directory.\n\n"
                f"Path: {project_path}\n\n"
                "Do you want to generate LICENSE anyway?"
            )
            if not response:
                return
        
        # Check if LICENSE already exists
        if (project_path / "LICENSE").exists():
            response = messagebox.askyesno(
                "Overwrite?", 
                "LICENSE file already exists.\nDo you want to overwrite it?"
            )
            if not response:
                return
        
        # Run in background thread
        thread = threading.Thread(
            target=self._generate_license_thread,
            args=(project_path,),
            daemon=True
        )
        thread.start()

    def _generate_license_thread(self, project_path):
        """Background thread for generating license"""
        try:
            # Generate license
            success = self.run_gen_license(project_path)
            
            # Update UI in main thread
            self.root.after(0, lambda: self._handle_license_result(success, project_path))
        
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror(
                "Error", 
                f"Exception while generating LICENSE:\n{str(e)}"
            ))

    def _handle_license_result(self, success, project_path):
        """Handle license generation result in main thread"""
        if success:
            messagebox.showinfo(
                "Success", 
                f"✅ LICENSE file generated successfully!\n\n"
                f"📁 Location: {project_path / 'LICENSE'}"
            )
        else:
            messagebox.showerror(
                "Error", 
                "❌ Failed to generate LICENSE file.\n\nCheck the console/logs for details."
            )

    def _generate_readme_thread(self, project_path):
        """Thread function for generating README"""
        self.log_message(f"Generating README documentation for: {project_path}")
        
        # Update generator with project path
        self.project_generator = ProjectGenerator(project_path)
        
        success = self.run_gen_readme(project_path)
        
        if success:
            self.log_message("README documentation generated successfully!", "SUCCESS")
            messagebox.showinfo("Success", "README documentation generated successfully!")
        else:
            self.log_message("Failed to generate README documentation!", "ERROR")
            messagebox.showerror("Error", "Failed to generate README documentation!")
                
    def initialize_gen_brand(self, project_path):
        """Initialize/Generate branding assets"""
        self.log_message("🎨 Initializing/Generating branding assets...")
        
        # Check if gen_brand.py exists in scripts directory
        scripts_dir = Path(__file__).parent.parent / "scripts"
        gen_brand_script = scripts_dir / "gen_brand.py"
        
        if not gen_brand_script.exists():
            self.log_message("❌ gen_brand.py not found in scripts directory", "ERROR")
            return False
        
        try:
            # Run gen_brand.py
            import subprocess
            result = subprocess.run(
                [sys.executable, str(gen_brand_script)],
                cwd=str(project_path),
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            if result.returncode == 0:
                self.log_message("✅ Branding assets generated successfully!", "SUCCESS")
                self.log_message(f"Output: {result.stdout}")
                
                # Check if branding assets were created
                brand_dir = project_path / "assets" / "brand"
                if brand_dir.exists():
                    brand_files = list(brand_dir.glob("*"))
                    self.log_message(f"📁 Branding assets created: {len(brand_files)} files in {brand_dir}")
                else:
                    self.log_message(f"⚠️ Branding directory may not have been created", "WARNING")
                
                return True
            else:
                self.log_message(f"❌ Failed to generate branding assets", "ERROR")
                if result.stderr:
                    self.log_message(f"Error: {result.stderr[:500]}")
                return False
                
        except Exception as e:
            self.log_message(f"❌ Exception while running gen_brand.py: {e}", "ERROR")
            return False

    def create_logs_tab(self):
        """Create logs/output tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📋 Logs")
        
        # Log text widget
        self.log_text = scrolledtext.ScrolledText(tab,
                                                wrap=tk.WORD,
                                                font=("Consolas", 10),
                                                height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Log controls
        control_frame = ttk.Frame(tab)
        control_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(control_frame,
                text="🗑️ Clear Logs",
                command=self.clear_logs).pack(side=tk.LEFT)
        
        ttk.Button(control_frame,
                text="💾 Save Logs",
                command=self.save_logs).pack(side=tk.LEFT, padx=10)
        
        ttk.Button(control_frame,
                text="📋 Copy",
                command=self.copy_logs).pack(side=tk.RIGHT)

    def clear_logs(self):
        """Clear all logs"""
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def save_logs(self):
        """Save logs to file"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                content = self.log_text.get(1.0, tk.END)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.log_message(f"Logs saved to {file_path}", "SUCCESS")
            except Exception as e:
                self.log_message(f"Failed to save logs: {e}", "ERROR")

    def copy_logs(self):
        """Copy logs to clipboard"""
        content = self.log_text.get(1.0, tk.END)
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        self.log_message("Logs copied to clipboard", "SUCCESS")

    def log_message(self, message, level="INFO"):
        """Add message to log"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        if level == "ERROR":
            tag = "error"
            prefix = f"[{timestamp}] ❌ ERROR: "
        elif level == "WARNING":
            tag = "warning"
            prefix = f"[{timestamp}] ⚠️  WARNING: "
        elif level == "SUCCESS":
            tag = "success"
            prefix = f"[{timestamp}] ✅ SUCCESS: "
        else:
            tag = "info"
            prefix = f"[{timestamp}] ℹ️  INFO: "
        
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, prefix + message + "\n")
        
        # Apply tags for coloring
        start_idx = self.log_text.index(f"end-{len(message)+len(prefix)+1}c")
        end_idx = self.log_text.index("end-1c")
        
        # Configure tags
        self.log_text.tag_config("error", foreground="red")
        self.log_text.tag_config("warning", foreground="orange")
        self.log_text.tag_config("success", foreground="green")
        self.log_text.tag_config("info", foreground="blue")
        
        self.log_text.tag_add(tag, start_idx, end_idx)
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)
        
        # Update UI
        self.root.update_idletasks()
    
    def create_build_tab(self):
        """Create build/installer tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🔨 Build")
        
        # Build settings
        settings_frame = ttk.LabelFrame(tab, text="Build Settings", padding=15)
        settings_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Project path
        ttk.Label(settings_frame,
                text="Project to Build:",
                font=("Segoe UI", 10, "bold")).grid(row=0, column=0,
                                                    sticky=tk.W, pady=5)
        
        build_path_frame = ttk.Frame(settings_frame)
        build_path_frame.grid(row=0, column=1, sticky=tk.W+tk.E,
                            pady=5, padx=(10, 0), columnspan=2)
        
        self.build_path_var = tk.StringVar(value=str(self.current_project_path))
        self.build_path_entry = ttk.Entry(build_path_frame,
                                        textvariable=self.build_path_var,
                                        width=50,
                                        font=("Segoe UI", 10))
        self.build_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(build_path_frame,
                text="Browse",
                command=self.browse_build_project,
                width=10).pack(side=tk.RIGHT, padx=(10, 0))
        
        # Quick branding button (can be useful before building)
        quick_brand_frame = ttk.LabelFrame(tab, text="Quick Actions", padding=15)
        quick_brand_frame.pack(fill=tk.X, padx=10, pady=10)
        
        quick_buttons = ttk.Frame(quick_brand_frame)
        quick_buttons.pack(fill=tk.X)
        
        ttk.Button(quick_buttons,
                text="🎨 Update Branding",
                command=lambda: self.generate_branding_only_for_build_tab(),
                width=20).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(quick_buttons,
                text="📦 Check Assets",
                command=lambda: self.check_branding_assets(),
                width=20).pack(side=tk.LEFT, padx=5)
        
        # Build options
        options_frame = ttk.LabelFrame(tab, text="Build Options", padding=15)
        options_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.build_options = {
            "clean_build": tk.BooleanVar(value=True),
            "generate_nsi": tk.BooleanVar(value=True),
            "generate_win": tk.BooleanVar(value=True),
            "create_distribution": tk.BooleanVar(value=True)
        }
        
        ttk.Checkbutton(options_frame,
                    text="Clean build directory before building",
                    variable=self.build_options["clean_build"]).grid(row=0, column=0,
                                                                    sticky=tk.W, pady=5)
        
        ttk.Checkbutton(options_frame,
                    text="Generate NSIS installer script (gen_nsi.py)",
                    variable=self.build_options["generate_nsi"]).grid(row=1, column=0,
                                                                        sticky=tk.W, pady=5)
        
        ttk.Checkbutton(options_frame,
                    text="Generate Windows build files (gen_win.py)",
                    variable=self.build_options["generate_win"]).grid(row=2, column=0,
                                                                        sticky=tk.W, pady=5)
        
        ttk.Checkbutton(options_frame,
                    text="Create distribution package",
                    variable=self.build_options["create_distribution"]).grid(row=3, column=0,
                                                                            sticky=tk.W, pady=5)
        
        # Action buttons
        button_frame = ttk.Frame(tab)
        button_frame.pack(fill=tk.X, padx=10, pady=20)
        
        # Left side: Individual actions
        left_button_frame = ttk.Frame(button_frame)
        left_button_frame.pack(side=tk.LEFT)
        
        ttk.Button(left_button_frame,
                text="📝 Generate NSI Only",
                command=self.generate_nsi_only,
                width=20).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(left_button_frame,
                text="🪟 Generate WIN Only",
                command=self.generate_win_only,
                width=20).pack(side=tk.LEFT, padx=2)
        
        # Right side: Full build
        right_button_frame = ttk.Frame(button_frame)
        right_button_frame.pack(side=tk.RIGHT)
        
        ttk.Button(right_button_frame,
                text="🔨 Full Build",
                style='Large.TButton',
                command=self.build_project).pack(side=tk.RIGHT, padx=5)
    
    def log_message(self, message, level="INFO"):
        """Add message to log"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        if level == "ERROR":
            tag = "error"
            prefix = f"[{timestamp}] ❌ ERROR: "
        elif level == "WARNING":
            tag = "warning"
            prefix = f"[{timestamp}] ⚠️  WARNING: "
        elif level == "SUCCESS":
            tag = "success"
            prefix = f"[{timestamp}] ✅ SUCCESS: "
        else:
            tag = "info"
            prefix = f"[{timestamp}] ℹ️  INFO: "
        
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, prefix + message + "\n")
        
        # Apply tags for coloring
        start_idx = self.log_text.index(f"end-{len(message)+len(prefix)+1}c")
        end_idx = self.log_text.index("end-1c")
        
        # Configure tags
        self.log_text.tag_config("error", foreground="red")
        self.log_text.tag_config("warning", foreground="orange")
        self.log_text.tag_config("success", foreground="green")
        self.log_text.tag_config("info", foreground="blue")
        
        self.log_text.tag_add(tag, start_idx, end_idx)
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)
        
        # Update UI
        self.root.update_idletasks()


    def generate_nsi_only(self):
        """Generate only NSIS script"""
        project_path = Path(self.build_path_var.get())
        
        if not project_path.exists():
            messagebox.showerror("Error", f"Project path does not exist:\n{project_path}")
            return
        
        # Run in background thread
        thread = threading.Thread(
            target=self._generate_nsi_thread,
            args=(project_path,),
            daemon=True
        )
        thread.start()

    def _generate_nsi_thread(self, project_path):
        """Thread function for generating NSIS script"""
        self.log_message(f"Generating NSIS script for: {project_path}")
        
        # Update generator with project path
        self.project_generator = ProjectGenerator(project_path)
        
        success = self.project_generator.generate_nsi(project_path)
        
        if success:
            self.log_message("NSIS script generated successfully!", "SUCCESS")
            messagebox.showinfo("Success", "NSIS installer script generated successfully!")
        else:
            self.log_message("Failed to generate NSIS script!", "ERROR")
            messagebox.showerror("Error", "Failed to generate NSIS script!")

    def generate_win_only(self):
        """Generate only Windows build files"""
        project_path = Path(self.build_path_var.get())
        
        if not project_path.exists():
            messagebox.showerror("Error", f"Project path does not exist:\n{project_path}")
            return
        
        # Run in background thread
        thread = threading.Thread(
            target=self._generate_win_thread,
            args=(project_path,),
            daemon=True
        )
        thread.start()

    def _generate_win_thread(self, project_path):
        """Thread function for generating Windows build files"""
        self.log_message(f"Generating Windows build files for: {project_path}")
        
        # Update generator with project path
        self.project_generator = ProjectGenerator(project_path)
        
        # Run gen_win.py
        success = self.project_generator.run_script("gen_win.py", project_path)
        
        if success:
            self.log_message("Windows build files generated successfully!", "SUCCESS")
            messagebox.showinfo("Success", "Windows build files generated successfully!")
        else:
            self.log_message("Failed to generate Windows build files!", "ERROR")
            messagebox.showerror("Error", "Failed to generate Windows build files!")
    
    def clear_logs(self):
        """Clear all logs"""
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state=tk.DISABLED)
    
    def save_logs(self):
        """Save logs to file"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                content = self.log_text.get(1.0, tk.END)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.log_message(f"Logs saved to {file_path}", "SUCCESS")
            except Exception as e:
                self.log_message(f"Failed to save logs: {e}", "ERROR")
    
    def copy_logs(self):
        """Copy logs to clipboard"""
        content = self.log_text.get(1.0, tk.END)
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        self.log_message("Logs copied to clipboard", "SUCCESS")
    
    def browse_project(self):
        """Browse for project directory"""
        path = filedialog.askdirectory(
            title="Select Project Directory",
            initialdir=str(self.current_project_path)
        )
        
        if path:
            self.current_project_path = Path(path)
            self.project_label.config(text=f"📁 {self.current_project_path}")
            self.init_path_var.set(str(self.current_project_path))
            self.build_path_var.set(str(self.current_project_path))
            self.log_message(f"Project selected: {path}")
    
    def browse_init_project(self):
        """Browse for initialization project"""
        path = filedialog.askdirectory(
            title="Select Project to Initialize",
            initialdir=str(Path(self.init_path_var.get()))
        )
        
        if path:
            self.init_path_var.set(path)

    def select_all_scripts(self):
        """Select all scripts"""
        for var in self.scripts_vars.values():
            var.set(True)

    def clear_all_scripts(self):
        """Clear all script selections"""
        for var in self.scripts_vars.values():
            var.set(False)

    def update_tree(self):
        """Update project tree structure"""
        project_path = Path(self.init_path_var.get())
        
        if not project_path.exists():
            messagebox.showerror("Error", "Project path does not exist!")
            return
        
        # Create a simple tree structure
        tree_file = project_path / "PROJECT_TREE.txt"
        try:
            tree_content = self.generate_simple_tree(project_path)
            tree_file.write_text(tree_content, encoding='utf-8')
            self.log_message(f"Created project tree at {tree_file}", "SUCCESS")
        except Exception as e:
            self.log_message(f"Failed to create tree: {e}", "ERROR")

    def generate_simple_tree(self, path, prefix=""):
        """Generate a simple directory tree"""
        import os
        lines = []
        try:
            items = sorted(os.listdir(path))
            for i, item in enumerate(items):
                connector = "└── " if i == len(items) - 1 else "├── "
                lines.append(f"{prefix}{connector}{item}")
                
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    extension = "    " if i == len(items) - 1 else "│   "
                    lines.append(self.generate_simple_tree(item_path, prefix + extension))
        except:
            pass
        
        return "\n".join(lines)
    
    def browse_build_project(self):
        """Browse for build project"""
        path = filedialog.askdirectory(
            title="Select Project to Build",
            initialdir=str(Path(self.build_path_var.get()))
        )
        
        if path:
            self.build_path_var.set(path)
    
    def select_all_scripts(self):
        """Select all scripts"""
        for var in self.scripts_vars.values():
            var.set(True)
    
    def clear_all_scripts(self):
        """Clear all script selections"""
        for var in self.scripts_vars.values():
            var.set(False)
    
    def run_initialization(self):
        """Run initialization scripts"""
        project_path = Path(self.init_path_var.get())
        
        if not project_path.exists():
            messagebox.showerror("Error", f"Project path does not exist:\n{project_path}")
            return
        
        # Get selected scripts
        selected_scripts = [script for script, var in self.scripts_vars.items() 
                        if var.get()]
        
        if not selected_scripts:
            messagebox.showwarning("Warning", "No scripts selected!")
            return
        
        # Run in background thread
        thread = threading.Thread(
            target=self._run_initialization_thread,
            args=(project_path, selected_scripts),
            daemon=True
        )
        thread.start()

    def _run_initialization_thread(self, project_path, scripts):
        """Thread function for running initialization"""
        self.log_message(f"Starting initialization for: {project_path}")
        
        success_count = 0
        total_scripts = len(scripts)
        
        for i, script in enumerate(scripts, 1):
            self.log_message(f"Running {script} ({i}/{total_scripts})...")
            
            try:
                success = self.initialize_script(script, project_path)
                
                if success:
                    self.log_message(f"{script} completed successfully", "SUCCESS")
                    success_count += 1
                else:
                    self.log_message(f"{script} failed", "ERROR")
                    
            except Exception as e:
                self.log_message(f"Error running {script}: {e}", "ERROR")
        
        # Summary
        if success_count == total_scripts:
            self.log_message(f"✅ All {success_count} scripts completed successfully!", "SUCCESS")
            messagebox.showinfo("Success", 
                            f"Initialization completed successfully!\n" +
                            f"{success_count}/{total_scripts} scripts executed.")
        else:
            self.log_message(f"⚠️  {success_count}/{total_scripts} scripts completed", "WARNING")
            messagebox.showwarning("Partial Success",
                                f"Initialization partially completed.\n" +
                                f"{success_count}/{total_scripts} scripts executed.")
        
    def update_tree(self):
        """Update project tree structure"""
        project_path = Path(self.init_path_var.get())
        
        if not project_path.exists():
            messagebox.showerror("Error", "Project path does not exist!")
            return
        
        # Run gen_tree.py if it exists
        scripts_dir = PACKAGE_DIR / "scripts"
        tree_script = scripts_dir / "gen_tree.py"
        
        if tree_script.exists():
            self.log_message("Generating project tree...")
            success = self.project_generator.run_script("gen_tree.py", project_path)
            
            if success:
                self.log_message("Project tree updated successfully", "SUCCESS")
            else:
                self.log_message("Failed to update project tree", "ERROR")
        else:
            self.log_message("gen_tree.py not found in scripts directory", "WARNING")
            # Create a simple tree
            tree_file = project_path / "PROJECT_TREE.txt"
            try:
                tree_content = self.generate_simple_tree(project_path)
                tree_file.write_text(tree_content, encoding='utf-8')
                self.log_message(f"Created simple project tree at {tree_file}", "SUCCESS")
            except Exception as e:
                self.log_message(f"Failed to create tree: {e}", "ERROR")
    
    def generate_simple_tree(self, path, prefix=""):
        """Generate a simple directory tree"""
        lines = []
        try:
            items = sorted(path.iterdir())
            for i, item in enumerate(items):
                connector = "└── " if i == len(items) - 1 else "├── "
                lines.append(f"{prefix}{connector}{item.name}")
                
                if item.is_dir():
                    extension = "    " if i == len(items) - 1 else "│   "
                    lines.append(self.generate_simple_tree(item, prefix + extension))
        except:
            pass
        
        return "\n".join(lines)
    
    def build_project(self):
        """Build the project"""
        project_path = Path(self.build_path_var.get())
        
        if not project_path.exists():
            messagebox.showerror("Error", f"Project path does not exist:\n{project_path}")
            return
        
        # Run build in background thread
        thread = threading.Thread(
            target=self._build_project_thread,
            args=(project_path,),
            daemon=True
        )
        thread.start()
    
    def _build_project_thread(self, project_path):
        """Thread function for building project"""
        self.log_message(f"Starting build for: {project_path}")
        
        # Update generator with project path
        self.project_generator = ProjectGenerator(project_path)
        
        # Check which scripts to run based on checkboxes
        scripts_to_run = []
        
        if self.build_options["generate_nsi"].get():
            scripts_to_run.append("gen_nsi.py")
        
        if self.build_options["generate_win"].get():
            scripts_to_run.append("gen_win.py")
        
        if not scripts_to_run:
            self.log_message("No build scripts selected!", "WARNING")
            messagebox.showwarning("Warning", "No build options selected!")
            return
        
        success = True
        for script in scripts_to_run:
            self.log_message(f"Running {script}...")
            if not self.project_generator.run_script(script, project_path):
                success = False
                self.log_message(f"Failed to run {script}", "ERROR")
        
        if success:
            self.log_message("Build completed successfully!", "SUCCESS")
            messagebox.showinfo("Success", "Project built successfully!")
        else:
            self.log_message("Build failed!", "ERROR")
            messagebox.showerror("Error", "Build failed! Check logs for details.")
    
    def create_project(self):
        """Create a new project"""
        # Open a dialog to get project details
        dialog = tk.Toplevel(self.root)
        dialog.title("Create New Project")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'{width}x{height}+{x}+{y}')
        
        # Project name
        ttk.Label(dialog, text="Project Name:", 
                 font=("Segoe UI", 11, "bold")).pack(pady=(20, 5), padx=20, anchor=tk.W)
        
        project_name_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=project_name_var,
                 font=("Segoe UI", 11)).pack(fill=tk.X, padx=20, pady=(0, 15))
        
        # Location
        ttk.Label(dialog, text="Location:", 
                 font=("Segoe UI", 11, "bold")).pack(pady=(10, 5), padx=20, anchor=tk.W)
        
        location_frame = ttk.Frame(dialog)
        location_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        location_var = tk.StringVar(value=str(Path.cwd()))
        ttk.Entry(location_frame, textvariable=location_var,
                 font=("Segoe UI", 10)).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(location_frame, text="Browse",
                  command=lambda: self.browse_location(location_var)).pack(side=tk.RIGHT, padx=(10, 0))
        
        # Category
        ttk.Label(dialog, text="Category:", 
                 font=("Segoe UI", 11, "bold")).pack(pady=(10, 5), padx=20, anchor=tk.W)
        
        category_var = tk.StringVar()
        categories = [
            "Productivity & Office",
            "Development Tools", 
            "Creative & Multimedia",
            "Communication",
            "Utilities & Security",
            "Business & Enterprise"
        ]
        
        category_combo = ttk.Combobox(dialog, textvariable=category_var,
                                     values=categories,
                                     font=("Segoe UI", 10),
                                     state="readonly")
        category_combo.pack(fill=tk.X, padx=20, pady=(0, 15))
        category_combo.current(0)
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Button(button_frame, text="Cancel",
                  command=dialog.destroy).pack(side=tk.LEFT)
        
        ttk.Button(button_frame, text="Create",
                  style='Accent.TButton',
                  command=lambda: self.execute_create_project(
                      project_name_var.get(),
                      category_var.get(),
                      location_var.get(),
                      dialog
                  )).pack(side=tk.RIGHT)
    
    def browse_location(self, location_var):
        """Browse for location"""
        path = filedialog.askdirectory(
            title="Select Project Location",
            initialdir=location_var.get()
        )
        
        if path:
            location_var.set(path)
    
    def execute_create_project(self, project_name, category, location, dialog):
        """Execute project creation"""
        if not project_name:
            messagebox.showerror("Error", "Please enter a project name!")
            return
        
        dialog.destroy()
        
        # Run in background thread
        thread = threading.Thread(
            target=self._create_project_thread,
            args=(project_name, category, location),
            daemon=True
        )
        thread.start()
    
    def _create_project_thread(self, project_name, category, location):
        """Thread function for creating project"""
        self.log_message(f"Creating project '{project_name}'...")
        
        try:
            category_data = {"name": category}
            result = self.project_generator.create_structure(project_name, category_data, location)
            
            self.log_message(f"Project created at: {result}", "SUCCESS")
            
            # Ask if user wants to open the new project
            if messagebox.askyesno("Success", 
                                 f"Project '{project_name}' created successfully!\n\n" +
                                 f"Open project?"):
                self.current_project_path = Path(result)
                self.project_label.config(text=f"📁 {self.current_project_path}")
                self.init_path_var.set(str(self.current_project_path))
                self.build_path_var.set(str(self.current_project_path))
                self.log_message(f"Switched to project: {project_name}")
                
        except Exception as e:
            self.log_message(f"Failed to create project: {e}", "ERROR")
            messagebox.showerror("Error", f"Failed to create project:\n{e}")
    
    def quick_initialize(self):
        """Quick initialize current project"""
        response = messagebox.askyesno("Quick Initialize",
                                      f"Initialize project at:\n{self.current_project_path}\n\n" +
                                      "This will run all initialization scripts.")
        
        if response:
            self.notebook.select(1)  # Switch to Initialize tab
            self.select_all_scripts()
            self.run_initialization()
    
    def show_initialize_tab(self):
        """Show the initialize tab"""
        self.notebook.select(1)  # Tab index 1 is Initialize tab
    
    def open_project_folder(self):
        """Open current project folder"""
        try:
            os.startfile(self.current_project_path)
        except:
            try:
                subprocess.run(['explorer', str(self.current_project_path)], shell=True)
            except:
                self.log_message("Could not open project folder", "ERROR")
    
    def open_docs(self):
        """Open documentation"""
        webbrowser.open("https://github.com/amatak-org/amatak_winapp")
    
    def show_about(self):
        """Show about dialog"""
        about_text = f"""Amatak WinApp Generator v{get_version()}

A comprehensive toolkit for creating Windows 
application installers and projects.

Features:
• Create complete Windows application projects
• Generate professional branding assets
• Build NSIS-based installers
• Easy-to-use graphical interface
• Command-line support

Author: Amatak Development Team
License: MIT
GitHub: https://github.com/amatak-org/amatak_winapp
"""
        
        messagebox.showinfo("About Amatak WinApp", about_text)
    
    def on_closing(self):
        """Handle window closing"""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.root.destroy()

def gui_main():
    """Main GUI entry point"""
    root = tk.Tk()
    
    # Set theme if available
    try:
        root.tk.call("source", "azure.tcl")
        root.tk.call("set_theme", "dark")
    except:
        pass
    
    # Create and run GUI
    app = WinAppGUI(root)
    root.mainloop()

if __name__ == "__main__":
    gui_main()