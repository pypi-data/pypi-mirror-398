import sys
import subprocess
import os
import glob

def start():
    py_files = glob.glob("*.py")

    if not py_files:
        print("Error: No .py files found in this directory.")
        return

    for file_path in py_files:
        try:
            print(f"Building: {file_path} with all assets...")
            
            subprocess.run([
                "pyinstaller",
                "--onefile",
                "--add-data", ".;.",
                file_path
            ], check=True)
            
        except subprocess.CalledProcessError:
            print(f"Failed to build: {file_path}")
        except FileNotFoundError:
            print("Error: PyInstaller not found. Install it with: pip install pyinstaller")
            break

if __name__ == "__main__":
    start()