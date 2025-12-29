import sys
import subprocess
import os
import glob

def create_readme():
    print("You don't have readme.txt but it is not required.")
    print('Do you want to add readme.txt directly through the console? (Example: y "My Cool Game")')
    user_input = input("Choice: ").strip()
    if user_input.lower().startswith('y'):
        parts = user_input.split(' ', 1)
        name = parts[1].strip('"') if len(parts) > 1 else "My Project"
        print(f'Enter a description for "{name}":')
        desc = input()
        with open("readme.txt", "w", encoding="utf-8") as f:
            f.write(f"Project: {name}\n")
            f.write(f"Description: {desc}\n")
            f.write("\nCreated with Tole-Tool")
        print("readme.txt created successfully!")

def start():
    if not os.path.exists("readme.txt"):
        create_readme()
    py_files = glob.glob("*.py")
    if not py_files:
        print("Error: No .py files found.")
        return
    for file_path in py_files:
        try:
            print(f"Building: {file_path}")
            subprocess.run(["pyinstaller", "--onefile", "--add-data", ".;.", file_path], check=True)
            print("Succeed!")
        except Exception as e:
            print(f"Failed: {file_path}")

if name == "main":
    start()