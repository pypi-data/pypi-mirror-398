import sys
import subprocess
import os
import glob

def start():
    py_files = glob.glob("*.py")

    if not py_files:
        print("Error: No .py files found in this directory.")
        return

    print(f"Found {len(py_files)} files: {', '.join(py_files)}")
    
    for file_path in py_files:
        try:
            print(f"\n--- Processing: {file_path} ---")
            subprocess.run([
                "pyinstaller", 
                "--onefile", 
                "--noconsole", 
                file_path
            ], check=True)
            print(f"Success! {file_path} converted to EXE.")
        except subprocess.CalledProcessError:
            print(f"Error: Failed to convert {file_path}.")
        except FileNotFoundError:
            print("Error: PyInstaller not installed. Run: pip install pyinstaller")
            break

    print("\nAll done! Check the 'dist' folder.")

if name == "main":
    start()