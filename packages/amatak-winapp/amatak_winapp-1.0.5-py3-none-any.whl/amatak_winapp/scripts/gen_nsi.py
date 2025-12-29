# gen_nsi.py - Fixed version without emojis
import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Get the current working directory (project directory)
PROJECT_ROOT = Path.cwd()

# Configuration - all paths relative to PROJECT_ROOT
VERSION_FILE = PROJECT_ROOT / "VERSION.txt"
NSIS_OUTPUT_PATH = PROJECT_ROOT / "installer" / "win_installer.nsi"
CONFIG_FILE = PROJECT_ROOT / "config.json"

# Exclude patterns
EXCLUDE_DIRS = {".venv", ".git", "__pycache__", ".idea", ".vscode", "installer", "dist", "build"}
EXCLUDE_FILES = {"gen_nsi.py", "gen_readme.py", "gen_win.py", "_init_scanner.py", ".gitignore", "tree.txt", "*.pyc", "*.pyo"}

def get_version():
    """Read version from VERSION.txt"""
    try:
        if VERSION_FILE.exists():
            return VERSION_FILE.read_text(encoding="utf-8").strip()
    except Exception:
        pass
    return "1.0.0"

def detect_current_app():
    """
    Detect whether we're building the builder or a generated app
    Returns: (app_name, is_builder)
    """
    # Check for winapp.py file - if it exists, this is likely the builder
    if (PROJECT_ROOT / "winapp.py").exists():
        return "Amatak WinApp Generator", True
    
    # Check for amatak_winapp package directory
    if (PROJECT_ROOT / "amatak_winapp").exists():
        return "Amatak WinApp Generator", True
    
    # Check config.json for project name
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                app_name = config.get('project_name', PROJECT_ROOT.name)
                return app_name, False
        except:
            pass
    
    # Default to project directory name
    return PROJECT_ROOT.name, False

def get_registry_key(app_name):
    """Generate registry key from app name"""
    # Remove spaces and special characters for registry key
    registry_key = ''.join(c for c in app_name if c.isalnum())
    return registry_key

def get_install_dir(app_name):
    """Generate install directory path"""
    if "Amatak WinApp Generator" in app_name:
        return f"$PROGRAMFILES\\Amatak Holdings Pty Ltd\\Amatak WinApp Generator"
    else:
        return f"$PROGRAMFILES\\Amatak Holdings Pty Ltd\\{app_name}"

def get_outfile_name(app_name, version):
    """Generate output installer filename"""
    if "Amatak WinApp Generator" in app_name:
        return f"Amatak_WinApp_Generator_Setup_v{version}.exe"
    else:
        # For generated apps, use the app name
        safe_name = app_name.replace(' ', '_').replace('&', 'And')
        return f"Amatak_{safe_name}_Setup_v{version}.exe"

def scan_project_files():
    """Scan project files and return list of relative paths"""
    files_to_install = []
    
    print(f"Scanning project directory: {PROJECT_ROOT}")
    
    for root, dirs, files in os.walk(PROJECT_ROOT):
        # Remove excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        # Skip excluded directories entirely
        root_path = Path(root)
        if any(excl_dir in str(root_path) for excl_dir in EXCLUDE_DIRS):
            continue
            
        for file in files:
            # Skip excluded files
            if file in EXCLUDE_FILES or file.endswith(".pyc") or file.endswith(".pyo"):
                continue
                
            # Skip files matching exclude patterns
            if any(file.endswith(pattern.replace("*", "")) for pattern in EXCLUDE_FILES if "*" in pattern):
                continue
            
            # Get relative path from project root
            try:
                file_path = Path(root) / file
                rel_path = file_path.relative_to(PROJECT_ROOT)
                files_to_install.append(str(rel_path))
            except ValueError:
                # File not relative to project root (shouldn't happen)
                continue
    
    print(f"Found {len(files_to_install)} files to install")
    return sorted(files_to_install)

def generate_nsi():
    """Generate NSIS installer script - DYNAMIC VERSION"""
    version = get_version()
    year = datetime.now().year
    
    # Detect current app context
    currentapp, is_builder = detect_current_app()
    print(f"\nBuilding installer for: {currentapp}")
    print(f"Context: {'Builder' if is_builder else 'Generated App'}")
    
    # Get list of files to install
    files_list = scan_project_files()
    
    if not files_list:
        print("ERROR: No files found to install! Check your project directory.")
        return False
    
    # Check for required assets
    icon_path = PROJECT_ROOT / "assets" / "brand" / "brand.ico"
    header_path = PROJECT_ROOT / "assets" / "brand" / "brand_installer.bmp"
    
    if not icon_path.exists():
        print(f"Warning: Icon not found at {icon_path}")
        # Try alternative locations
        alt_icon = PROJECT_ROOT / "assets" / "brand.ico"
        if alt_icon.exists():
            icon_path = alt_icon
            print(f"  Using alternative: {icon_path}")
    
    if not header_path.exists():
        print(f"Warning: Header image not found at {header_path}")
        # Try alternative locations
        alt_header = PROJECT_ROOT / "assets" / "brand_installer.bmp"
        if alt_header.exists():
            header_path = alt_header
            print(f"  Using alternative: {header_path}")
    
    # Get relative paths for NSIS (relative to installer/ folder)
    icon_relative = "..\\assets\\brand\\brand.ico"
    header_relative = "..\\assets\\brand\\brand_installer.bmp"

    # Generate installer metadata
    registry_key = get_registry_key(currentapp)
    install_dir = get_install_dir(currentapp)
    outfile_name = get_outfile_name(currentapp, version)
    
    # SIMPLIFIED NSIS TEMPLATE - DYNAMIC
    nsi_content = f"""; ============================================
; {currentapp} Installer ({year})
; Company: Amatak Holdings Pty Ltd
; ============================================
!include "MUI2.nsh"

Name "{currentapp} v{version}"
OutFile "{outfile_name}"
InstallDir "{install_dir}"
InstallDirRegKey HKLM "Software\\{registry_key}" "Install_Dir"
RequestExecutionLevel admin
ShowInstDetails show
BrandingText "Amatak Holdings Pty Ltd © {year}"

!define MUI_ICON "{icon_relative}"
!define MUI_UNICON "{icon_relative}"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "{header_relative}"

Var StartMenuFolder

; --- PAGES ---
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_STARTMENU Application $StartMenuFolder
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

; =========== MAIN SECTION ===========
Section "MainSection" SEC01
    SetOutPath "$INSTDIR"
    
    ; Create directories and install files
"""
    
    # Add file installation commands
    processed_dirs = set()
    current_dir = None
    
    for file_path in files_list:
        win_path = file_path.replace('/', '\\')
        
        # Create directory if needed
        if '\\' in win_path:
            dir_path = '\\'.join(win_path.split('\\')[:-1])
            if dir_path and dir_path not in processed_dirs:
                nsi_content += f'    CreateDirectory "$INSTDIR\\{dir_path}"\n'
                processed_dirs.add(dir_path)
    
    # Install files
    for file_path in files_list:
        win_path = file_path.replace('/', '\\')
        
        # Set output directory
        if '\\' in win_path:
            dir_path = '\\'.join(win_path.split('\\')[:-1])
            if dir_path != current_dir:
                nsi_content += f'    SetOutPath "$INSTDIR\\{dir_path}"\n'
                current_dir = dir_path
        else:
            if current_dir != "":
                nsi_content += f'    SetOutPath "$INSTDIR"\n'
                current_dir = ""
        
        # Install file
        nsi_relative = "..\\" + win_path
        nsi_content += f'    File "{nsi_relative}"\n'
    
    # Continue with the rest of the script - DYNAMIC for builder vs generated apps
    if is_builder:
        # Builder-specific launcher script
        nsi_content += f"""
    ; Install VERSION.txt if it exists
    SetOutPath "$INSTDIR"
    File "..\\VERSION.txt"
    
    ; Create batch launcher for builder
    FileOpen $0 "$INSTDIR\\winapp.bat" w
    FileWrite $0 "@echo off$\\r$\\n"
    FileWrite $0 "echo ========================================$\\r$\\n"
    FileWrite $0 "echo   {currentapp} v{version}$\\r$\\n"
    FileWrite $0 "echo ========================================$\\r$\\n"
    FileWrite $0 "echo.$\\r$\\n"
    FileWrite $0 'cd /d "%~dp0"$\\r$\\n'
    FileWrite $0 "echo.$\\r$\\n"
    FileWrite $0 "echo Looking for Python...$\\r$\\n"
    FileWrite $0 "set FOUND=0$\\r$\\n"
    FileWrite $0 "py --version >nul 2>&1$\\r$\\n"
    FileWrite $0 "if not errorlevel 1 ($\\r$\\n"
    FileWrite $0 "  echo Found: Using py launcher$\\r$\\n"
    FileWrite $0 "  py -m amatak_winapp.winapp %*$\\r$\\n"
    FileWrite $0 "  set FOUND=1$\\r$\\n"
    FileWrite $0 "  goto :end$\\r$\\n"
    FileWrite $0 ")$\\r$\\n"
    FileWrite $0 "python --version >nul 2>&1$\\r$\\n"
    FileWrite $0 "if not errorlevel 1 ($\\r$\\n"
    FileWrite $0 "  echo Found: Using python command$\\r$\\n"
    FileWrite $0 "  python -m amatak_winapp.winapp %*$\\r$\\n"
    FileWrite $0 "  set FOUND=1$\\r$\\n"
    FileWrite $0 "  goto :end$\\r$\\n"
    FileWrite $0 ")$\\r$\\n"
    FileWrite $0 "python3 --version >nul 2>&1$\\r$\\n"
    FileWrite $0 "if not errorlevel 1 ($\\r$\\n"
    FileWrite $0 "  echo Found: Using python3 command$\\r$\\n"
    FileWrite $0 "  python3 -m amatak_winapp.winapp %*$\\r$\\n"
    FileWrite $0 "  set FOUND=1$\\r$\\n"
    FileWrite $0 "  goto :end$\\r$\\n"
    FileWrite $0 ")$\\r$\\n"
    FileWrite $0 "echo.$\\r$\\n"
    FileWrite $0 "echo ERROR: Python not found!$\\r$\\n"
    FileWrite $0 "echo Please install Python 3.7+ from https://www.python.org/downloads/$\\r$\\n"
    FileWrite $0 "echo.$\\r$\\n"
    FileWrite $0 "pause$\\r$\\n"
    FileWrite $0 ":end$\\r$\\n"
    FileWrite $0 "if %FOUND%==1 ($\\r$\\n"
    FileWrite $0 "  if errorlevel 1 ($\\r$\\n"
    FileWrite $0 "    echo.$\\r$\\n"
    FileWrite $0 "    echo Command failed with error code %ERRORLEVEL%$\\r$\\n"
    FileWrite $0 "    pause$\\r$\\n"
    FileWrite $0 "  )$\\r$\\n"
    FileWrite $0 ")$\\r$\\n"
    FileClose $0
    
    ; Create GUI launcher for builder
    FileOpen $0 "$INSTDIR\\launch_gui.pyw" w
    FileWrite $0 'import sys$\\r$\\n'
    FileWrite $0 'import os$\\r$\\n'
    FileWrite $0 'sys.path.insert(0, os.path.dirname(__file__))$\\r$\\n'
    FileWrite $0 'try:$\\r$\\n'
    FileWrite $0 '    from amatak_winapp.gui.winapp_gui import gui_main$\\r$\\n'
    FileWrite $0 '    gui_main()$\\r$\\n'
    FileWrite $0 'except Exception as e:$\\r$\\n'
    FileWrite $0 '    import tkinter as tk$\\r$\\n'
    FileWrite $0 '    from tkinter import messagebox$\\r$\\n'
    FileWrite $0 '    tk.Tk().withdraw()$\\r$\\n'
    FileWrite $0 '    messagebox.showerror("Error", f"Failed to start: {{e}}")$\\r$\\n'
    FileWrite $0 '    sys.exit(1)$\\r$\\n'
    FileClose $0
"""
    else:
        # Generated app launcher script
        nsi_content += f"""
    ; Install VERSION.txt if it exists
    SetOutPath "$INSTDIR"
    File "..\\VERSION.txt"
    
    ; Create batch launcher for generated app
    FileOpen $0 "$INSTDIR\\run.bat" w
    FileWrite $0 "@echo off$\\r$\\n"
    FileWrite $0 "echo ========================================$\\r$\\n"
    FileWrite $0 "echo   {currentapp} v{version}$\\r$\\n"
    FileWrite $0 "echo ========================================$\\r$\\n"
    FileWrite $0 "echo.$\\r$\\n"
    FileWrite $0 'cd /d "%~dp0"$\\r$\\n'
    FileWrite $0 "echo Starting {currentapp}...$\\r$\\n"
    FileWrite $0 "echo.$\\r$\\n"
    FileWrite $0 "py main.py %*$\\r$\\n"
    FileWrite $0 "if errorlevel 1 ($\\r$\\n"
    FileWrite $0 "  echo.$\\r$\\n"
    FileWrite $0 "  echo Application failed with error code %ERRORLEVEL%$\\r$\\n"
    FileWrite $0 "  pause$\\r$\\n"
    FileWrite $0 ")$\\r$\\n"
    FileClose $0
    
    ; Create Python launcher for generated app
    FileOpen $0 "$INSTDIR\\launch.pyw" w
    FileWrite $0 'import sys$\\r$\\n'
    FileWrite $0 'import os$\\r$\\n'
    FileWrite $0 'sys.path.insert(0, os.path.dirname(__file__))$\\r$\\n'
    FileWrite $0 'try:$\\r$\\n'
    FileWrite $0 '    import main$\\r$\\n'
    FileWrite $0 '    if hasattr(main, "main"):$\\r$\\n'
    FileWrite $0 '        sys.exit(main.main())$\\r$\\n'
    FileWrite $0 '    else:$\\r$\\n'
    FileWrite $0 '        print("No main() function found in main.py")$\\r$\\n'
    FileWrite $0 '        input("Press Enter to exit...")$\\r$\\n'
    FileWrite $0 'except Exception as e:$\\r$\\n'
    FileWrite $0 '    print(f"Error: {{e}}")$\\r$\\n'
    FileWrite $0 '    import traceback$\\r$\\n'
    FileWrite $0 '    traceback.print_exc()$\\r$\\n'
    FileWrite $0 '    input("Press Enter to exit...")$\\r$\\n'
    FileClose $0
"""
    
    # Common launcher scripts for both builder and generated apps
    nsi_content += f"""
    ; Create VBS wrapper - SIMPLIFIED AND CORRECT
    FileOpen $0 "$INSTDIR\\launch.vbs" w
    FileWrite $0 'Set WshShell = CreateObject("WScript.Shell")$\\r$\\n'
    FileWrite $0 'Set fso = CreateObject("Scripting.FileSystemObject")$\\r$\\n'
    FileWrite $0 'scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)$\\r$\\n'
    FileWrite $0 'batFile = scriptDir & "\\\\{"winapp.bat" if is_builder else "run.bat"}"$\\r$\\n'
    FileWrite $0 'WshShell.Run Chr(34) & batFile & Chr(34), 0, False$\\r$\\n'
    FileWrite $0 'Set WshShell = Nothing$\\r$\\n'
    FileWrite $0 'Set fso = Nothing$\\r$\\n'
    FileClose $0
    
    ; Also create a direct shortcut batch file (visible console)
    FileOpen $0 "$INSTDIR\\run-visible.bat" w
    FileWrite $0 '@echo off$\\r$\\n'
    FileWrite $0 'cd /d "%~dp0"$\\r$\\n'
    FileWrite $0 'call {"winapp.bat" if is_builder else "run.bat"}$\\r$\\n'
    FileWrite $0 'if errorlevel 1 pause$\\r$\\n'
    FileClose $0
    
    ; Write installation info
    WriteRegStr HKLM "Software\\{registry_key}" "Install_Dir" "$INSTDIR"
    WriteRegStr HKLM "Software\\{registry_key}" "Version" "{version}"
    
    ; Write uninstall info
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{registry_key}" "DisplayName" "{currentapp}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{registry_key}" "UninstallString" '"$INSTDIR\\uninstall.exe"'
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{registry_key}" "DisplayIcon" "$INSTDIR\\assets\\brand\\brand.ico"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{registry_key}" "DisplayVersion" "{version}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{registry_key}" "Publisher" "Amatak Holdings Pty Ltd"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{registry_key}" "URLInfoAbout" "https://github.com/amatak-org/amatak-winapp"
    
SectionEnd

Section "Shortcuts" SEC02
    !insertmacro MUI_STARTMENU_WRITE_BEGIN Application
    CreateDirectory "$SMPROGRAMS\\$StartMenuFolder"
    ; Create shortcut to VBS launcher (hidden console)
    CreateShortcut "$SMPROGRAMS\\$StartMenuFolder\\{currentapp}.lnk" "$INSTDIR\\launch.vbs" "" "$INSTDIR\\assets\\brand\\brand.ico" 0
    ; Create shortcut to visible console
    CreateShortcut "$SMPROGRAMS\\$StartMenuFolder\\{currentapp} (Console).lnk" "$INSTDIR\\run-visible.bat" "" "$INSTDIR\\assets\\brand\\brand.ico" 0
    ; Create shortcut to Python GUI launcher
    CreateShortcut "$SMPROGRAMS\\$StartMenuFolder\\{currentapp} GUI.lnk" "$INSTDIR\\{"launch_gui.pyw" if is_builder else "launch.pyw"}" "" "$INSTDIR\\assets\\brand\\brand.ico" 0
    CreateShortcut "$SMPROGRAMS\\$StartMenuFolder\\Uninstall.lnk" "$INSTDIR\\uninstall.exe" "" "$INSTDIR\\uninstall.exe" 0
    CreateShortcut "$DESKTOP\\{currentapp}.lnk" "$INSTDIR\\launch.vbs" "" "$INSTDIR\\assets\\brand\\brand.ico" 0
    !insertmacro MUI_STARTMENU_WRITE_END
SectionEnd

Section -Post
    WriteUninstaller "$INSTDIR\\uninstall.exe"
SectionEnd

Section "Uninstall"
    ; Remove shortcuts
    !insertmacro MUI_STARTMENU_GETFOLDER Application $StartMenuFolder
    Delete "$SMPROGRAMS\\$StartMenuFolder\\*.*"
    RMDir "$SMPROGRAMS\\$StartMenuFolder"
    Delete "$DESKTOP\\{currentapp}.lnk"
    
    ; Remove registry entries
    DeleteRegKey HKLM "Software\\{registry_key}"
    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{registry_key}"
    
    ; Remove files
    Delete "$INSTDIR\\{"winapp.bat" if is_builder else "run.bat"}"
    Delete "$INSTDIR\\launch.vbs"
    Delete "$INSTDIR\\run-visible.bat"
    Delete "$INSTDIR\\{"launch_gui.pyw" if is_builder else "launch.pyw"}"
    Delete "$INSTDIR\\uninstall.exe"
    
    ; Remove all other files
    RMDir /r "$INSTDIR"
SectionEnd

Function .onInit
    StrCpy $StartMenuFolder "{registry_key}"
FunctionEnd
"""
    
    try:
        # Create installer directory if it doesn't exist
        NSIS_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        with open(NSIS_OUTPUT_PATH, "w", encoding="utf-8") as f:
            f.write(nsi_content)
        
        print(f"\n[{year}] SUCCESS: NSIS installer script generated successfully!")
        print(f"   Application: {currentapp}")
        print(f"   Location: {NSIS_OUTPUT_PATH}")
        print(f"   Version: {version}")
        print(f"   Files to install: {len(files_list)}")
        
        # Show first few files as example
        if files_list:
            print(f"\nExample files to be installed:")
            for i, file_path in enumerate(files_list[:10]):
                print(f"   {i+1}. {file_path}")
            if len(files_list) > 10:
                print(f"   ... and {len(files_list) - 10} more files")
        
        # Show what will be created
        print(f"\nLauncher files that will be created:")
        if is_builder:
            print(f"   1. winapp.bat - Main console launcher")
            print(f"   2. launch_gui.pyw - GUI launcher (.pyw = no console)")
        else:
            print(f"   1. run.bat - Main console launcher")
            print(f"   2. launch.pyw - Python launcher (.pyw = no console)")
        print(f"   3. launch.vbs - Silent VBS launcher (for desktop shortcuts)")
        print(f"   4. run-visible.bat - Visible console launcher")
        
        print(f"\nShortcuts that will be created:")
        print(f"   Desktop: {currentapp}.lnk (silent)")
        print(f"   Start Menu:")
        print(f"     - {currentapp}.lnk (silent)")
        print(f"     - {currentapp} (Console).lnk (visible)")
        print(f"     - {currentapp} GUI.lnk (GUI)")
        print(f"     - Uninstall.lnk")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Error generating NSIS script: {e}")
        import traceback
        traceback.print_exc()
        return False



def compile_nsis():
    """Compile the NSIS script"""
    if not NSIS_OUTPUT_PATH.exists():
        print("ERROR: NSIS script not found. Generate it first.")
        return False
    

    # Detect app context for filename
    currentapp, is_builder = detect_current_app()
    version = get_version()
    outfile_name = get_outfile_name(currentapp, version)
    # Try to find makensis.exe
    nsis_paths = [
        r"C:\Program Files (x86)\NSIS\makensis.exe",
        r"C:\Program Files\NSIS\makensis.exe",
        r"C:\NSIS\makensis.exe",
        r"makensis.exe"  # If in PATH
    ]
    
    makensis = None
    for path in nsis_paths:
        if Path(path).exists():
            makensis = path
            break
    
    if not makensis:
        # Try to find in PATH
        import shutil
        makensis = shutil.which("makensis")
    
    if not makensis:
        print("WARNING: NSIS compiler (makensis.exe) not found.")
        print("   Install NSIS from: https://nsis.sourceforge.io/Download")
        print("   Or download portable version and add to PATH.")
        return False
    
    try:
        import subprocess
        print(f"\nCompiling installer with {makensis}...")
        print(f"   NSIS script: {NSIS_OUTPUT_PATH}")
        print(f"   Working dir: {PROJECT_ROOT}")
        
        # First, let's test if the script has any obvious syntax errors
        print("\nChecking NSIS script for common issues...")
        
        # Read the NSIS script to check for issues
        with open(NSIS_OUTPUT_PATH, 'r', encoding='utf-8') as f:
            nsis_content = f.read()
        
        # Common issues to check
        issues = []
        
        # Check for unclosed quotes
        quote_count = nsis_content.count('"')
        if quote_count % 2 != 0:
            issues.append(f"Unbalanced quotes (found {quote_count} quotes)")
        
        # Check for unclosed curly braces in macros
        lines = nsis_content.split('\n')
        for i, line in enumerate(lines, 1):
            if '${' in line and line.count('${') != line.count('}'):
                issues.append(f"Unbalanced curly braces on line {i}: {line[:50]}...")
        
        if issues:
            print("   Found potential issues:")
            for issue in issues:
                print(f"   WARNING: {issue}")
        else:
            print("   OK: No obvious syntax issues found")
        
        # Now try to compile with verbose output
        print("\nStarting NSIS compilation...")
        
        # Try different NSIS command line options to get more output
        cmd_options = [
            [makensis, "/V4", str(NSIS_OUTPUT_PATH)],  # Verbose level 4
            [makensis, "/V2", str(NSIS_OUTPUT_PATH)],  # Verbose level 2
            [makensis, str(NSIS_OUTPUT_PATH)]          # Default
        ]
        
        success = False
        last_error = ""
        
        for cmd in cmd_options:
            print(f"\n   Trying: {' '.join(cmd)}")
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    cwd=PROJECT_ROOT,
                    timeout=30  # 30 second timeout
                )
                
                if result.returncode == 0:
                    print("\nSUCCESS: Installer compiled successfully!")
                    
                    # Find the generated EXE
                    version = get_version()
                    exe_name = f"Amatak_WinApp_Generator_Setup_v{version}.exe"
                    exe_path = PROJECT_ROOT / exe_name
                    
                    if exe_path.exists():
                        size_mb = exe_path.stat().st_size / (1024 * 1024)
                        print(f"\nInstaller created: {exe_name}")
                        print(f"   Size: {size_mb:.2f} MB")
                        print(f"   Location: {exe_path}")
                        
                        # Show additional info
                        print(f"\nInstaller Details:")
                        print(f"   - Product: Amatak WinApp Generator")
                        print(f"   - Version: {version}")
                        print(f"   - Company: Amatak Holdings Pty Ltd")
                        print(f"   - Output: {exe_name}")
                    else:
                        print(f"WARNING: Installer EXE not found at expected location: {exe_path}")
                        print(f"   Check: {PROJECT_ROOT}\\*.exe")
                    
                    success = True
                    break
                else:
                    # Save error for analysis
                    last_error = result.stdout + "\n" + result.stderr
                    
                    # Try to extract meaningful error
                    error_lines = []
                    for line in (result.stdout + result.stderr).split('\n'):
                        line_lower = line.lower()
                        if any(keyword in line_lower for keyword in ['error', 'warning', 'failed', 'invalid', 'syntax']):
                            error_lines.append(line.strip())
                    
                    if error_lines:
                        print(f"\nERROR: Compilation errors found:")
                        for err in error_lines[:10]:  # Show first 10 errors
                            print(f"   {err}")
                    else:
                        print(f"\nERROR: Compilation failed (exit code: {result.returncode}) but no error details.")
                        
            except subprocess.TimeoutExpired:
                print(f"\nERROR: NSIS compilation timed out after 30 seconds")
                last_error = "Compilation timed out"
                break
            except Exception as e:
                print(f"\nERROR: Error running NSIS: {e}")
                last_error = str(e)
                break
        
        if not success:
            print(f"\nERROR: NSIS compilation failed!")
            print(f"\nTroubleshooting tips:")
            print("   1. Check if all required files exist (brand.ico, brand_installer.bmp)")
            print("   2. Run NSIS manually to see full error:")
            print(f'      "{makensis}" "{NSIS_OUTPUT_PATH}"')
            print("   3. Check for syntax errors in the generated NSIS file")
            print("   4. Make sure you have write permissions in the output directory")
            
            # Suggest manual compilation
            print(f"\nTry manual compilation:")
            print(f'   cd "{PROJECT_ROOT}"')
            print(f'   "{makensis}" "installer\\win_installer.nsi"')
        
        return success
    

            
    except Exception as e:
        print(f"ERROR: Failed to compile NSIS: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate NSIS installer for Amatak WinApp')
    parser.add_argument('--compile', '-c', action='store_true', help='Compile after generation')
    parser.add_argument('--version', '-v', action='store_true', help='Show version only')
    parser.add_argument('--files', '-f', action='store_true', help='List files to be installed')
    parser.add_argument('--test', '-t', action='store_true', help='Test NSIS syntax only')
    
    args = parser.parse_args()
    
    if args.version:
        print(f"Version: {get_version()}")
        return
    
    print("=" * 60)
    print("Amatak WinApp - NSIS Installer Generator")
    print("=" * 60)
    print(f"Project directory: {PROJECT_ROOT}")
    
    if args.files:
        files = scan_project_files()
        print(f"\nFiles to be installed ({len(files)}):")
        for i, file in enumerate(files, 1):
            print(f"  {i:3}. {file}")
        return
    
    success = generate_nsi()
    
    if success and (args.compile or args.test):
        print("\n" + "=" * 60)
        print("Compiling NSIS Installer")
        print("=" * 60)
        success = compile_nsis()
    
    if success:
        print("\n" + "=" * 60)
        print("SUCCESS: Process completed successfully!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("ERROR: Process failed!")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()