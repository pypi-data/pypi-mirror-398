import subprocess
import sys
import os

def winapp_init():
    """
    Calls scripts from the 'scripts/' folder, but executes them in the 
    context of the current working directory to ensure output stays in root.
    """
    # Define the specific order of scripts
    script_names = [
        "_init_scanner.py",
        "gen_readme.py",
        "gen_license_agreement.py",
        "license.py",
        "gen_tree.py",
        "gen_readme.py"
    ]

    # Determine the directory where this winapp_init.py file is located (scripts/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # The CWD where the terminal is currently at
    current_cwd = os.getcwd()

    print(f"Initializing winapp...")
    print(f"Target Directory (Output): {current_cwd}")

    for script in script_names:
        # Construct the full path to the script in the scripts/ folder
        script_path = os.path.join(script_dir, script)
        
        if os.path.exists(script_path):
            print(f"--- Running: {script} ---")
            try:
                # By default, subprocess.run uses the parent's CWD
                # This ensures the generated files are saved in the terminal's location.
                subprocess.run([sys.executable, script_path], check=True, cwd=current_cwd)
            except subprocess.CalledProcessError as e:
                print(f"Error: {script} failed with exit code {e.returncode}")
                sys.exit(1)
        else:
            print(f"Warning: Script not found: {script_path}")

if __name__ == "__main__":
    winapp_init()