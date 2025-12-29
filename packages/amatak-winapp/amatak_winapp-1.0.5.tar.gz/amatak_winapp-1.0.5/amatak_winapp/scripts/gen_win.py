import os
import subprocess
import winreg
import sys

# Configuration
NSI_SCRIPT = r"installer\win_installer.nsi"

def find_makensis():
    """Attempts to locate the makensis.exe executable on Windows."""
    # 1. Check if it's already in the system PATH
    try:
        subprocess.run(["makensis", "/VERSION"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return "makensis"
    except FileNotFoundError:
        pass

    # 2. Check standard Registry locations
    reg_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\NSIS"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Wow6432Node\NSIS")
    ]
    
    for hkey, subkey in reg_paths:
        try:
            with winreg.OpenKey(hkey, subkey) as key:
                install_dir = winreg.QueryValue(key, None)
                exe_path = os.path.join(install_dir, "makensis.exe")
                if os.path.exists(exe_path):
                    return exe_path
        except (OSError, FileNotFoundError):
            continue
            
    return None

def compile_installer():
    """Executes the NSIS compiler on the target script."""
    print("Searching for NSIS compiler...")
    makensis_path = find_makensis()
    
    if not makensis_path:
        print("Error: makensis.exe not found.")
        print("Please install NSIS (nsis.sourceforge.io) or add it to your PATH.")
        sys.exit(1)
        
    if not os.path.exists(NSI_SCRIPT):
        print(f"Error: Script not found at {NSI_SCRIPT}")
        sys.exit(1)

    print(f"Compiling {NSI_SCRIPT} using {makensis_path}...")
    
    # Run the compilation command
    # /V4 sets verbosity to all (useful for debugging)
    result = subprocess.run([makensis_path, "/V4", NSI_SCRIPT])
    
    if result.returncode == 0:
        print("\n" + "="*30)
        print("SUCCESS: Installer generated!")
        print("="*30)
    else:
        print("\n" + "!"*30)
        print(f"FAILED: Compilation failed with exit code {result.returncode}")
        print("!"*30)

if __name__ == "__main__":
    compile_installer()