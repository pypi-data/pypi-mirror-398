import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import os

def run_build(script_path, use_console):
    if not script_path:
        messagebox.showwarning("Warning", "Please select a Python file first!")
        return
    try:
        cmd = ["pyinstaller", "--onefile", "--add-data", ".;."]
        if not use_console:
            cmd.append("--noconsole")
        cmd.append(script_path)
        subprocess.run(cmd, check=True)
        messagebox.showinfo("Success", "EXE created in dist folder!")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def select_file(entry):
    path = filedialog.askopenfilename(filetypes=[("Python files", "*.py")])
    if path:
        entry.delete(0, tk.END)
        entry.insert(0, path)

def start_gui():
    root = tk.Tk()
    root.title("Tole-Tool 2.0.0 Alpha")
    root.geometry("450x300")
    tk.Label(root, text="Tole-Tool: GUI Builder (Alpha)", font=("Arial", 14, "bold")).pack(pady=10)
    tk.Label(root, text="Select your main Python script:").pack()
    file_frame = tk.Frame(root)
    file_frame.pack(pady=10)
    entry_path = tk.Entry(file_frame, width=40)
    entry_path.pack(side=tk.LEFT, padx=5)
    tk.Button(file_frame, text="Browse", command=lambda: select_file(entry_path)).pack(side=tk.LEFT)
    var_console = tk.BooleanVar(value=True)
    tk.Checkbutton(root, text="Show Console Window", variable=var_console).pack(pady=5)
    tk.Button(root, text="BUILD EXE", bg="#2ecc71", fg="white", font=("Arial", 12, "bold"), 
              command=lambda: run_build(entry_path.get(), var_console.get()), width=20, height=2).pack(pady=20)
    root.mainloop()

if name == "main":
    start_gui()