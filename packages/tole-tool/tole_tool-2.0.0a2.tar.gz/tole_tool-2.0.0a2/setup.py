from setuptools import setup, find_packages

setup(
    name="tole-tool",
    version="2.0.0a2",
    packages=find_packages(),
    install_requires=["pyinstaller"],
    entry_points={
        'console_scripts': [
            'tole=tole.tole_cli:start',
            'tole-gui=tole.tole_gui:start_gui'
        ]
    },
    author="wetoq",
    description="The simplest Python to EXE converter with GUI and auto-assets (Alpha).",
    long_description="""
# 🛠️ Tole-Tool 2.0.0 Alpha 2 🧪

**⚠️ Note: This is an Alpha version for testing.**

**Tole-Tool** is the fastest way to turn your Python script into a professional EXE file. Whether you love the speed of the console or the comfort of a window, we've got you covered!

---

### 📖 Choose Your Way

#### 🖼️ Method 1: The New GUI
1. Open CMD and type: `tole-gui`
2. Click **Browse** and select your `.py` file.
3. Click **BUILD EXE** and wait for the "Succeed!" message.

#### ⌨️ Method 2: Fast Console
1. Navigate to your folder in CMD (`cd ..` and `cd "your_folder"`).
2. Type: `tole`
3. Follow the prompts to create a `readme.txt`.

---

### 🔥 Why Tole-Tool?
* **📦 Auto-Bundle Assets**: Automatically packs all photos and sounds inside the EXE.
* **🖼️ New GUI**: Easy visual builder for beginners.
* **🚀 One-File Magic**: Everything compressed into one portable .exe.

---
### 💻 Installation
```bash
pip install tole-tool
Powered by PyInstaller engine. Created by wetoq.
""",
long_description_content_type="text/markdown",
url="https://pypi.org/project/tole-tool/",
classifiers=[
"Programming Language :: Python :: 3",
"License :: OSI Approved :: MIT License",
"Operating System :: Microsoft :: Windows",
],
)