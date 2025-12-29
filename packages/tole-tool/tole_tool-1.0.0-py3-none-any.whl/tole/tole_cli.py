import os
import subprocess
import sys

def start():
    print("\n--- TOLE CLI Distribution Tool ---")
    
    confirm = input("Do you want to start the porting process to EXE? (y/n): ").lower()
    if confirm != 'y':
        print("Operation cancelled.")
        sys.exit()

    script_path = input("Enter the path to your .py file: ").strip().replace('"', '')
    if not os.path.exists(script_path):
        print(f"Error: File not found at {script_path}")
        return

    output_dir = input("Enter the destination folder (e.g., C:/project): ").strip().replace('"', '')
    
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            print(f"Created directory: {output_dir}")
        except Exception as e:
            print(f"Error creating directory: {e}")
            return

    print(f"\nBuilding EXE for: {script_path}")
    print("Please wait, this may take a minute...")

    try:
        subprocess.run([
            "pyinstaller", 
            "--onefile", 
            "--noconsole", 
            "--distpath", output_dir,
            script_path
        ], check=True)
        
        print("\n" + "="*30)
        print("SUCCESS!")
        print(f"Your EXE is located in: {output_dir}")
        print("="*30)
        
    except subprocess.CalledProcessError:
        print("\nError: PyInstaller failed to build the project.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

if name == "main":
    start()