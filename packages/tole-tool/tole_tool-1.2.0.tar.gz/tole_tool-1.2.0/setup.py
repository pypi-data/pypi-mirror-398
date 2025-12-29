from setuptools import setup, find_packages

setup(
    name="tole-tool",
    version="1.2.0",
    packages=find_packages(),
    install_requires=["pyinstaller"],
    entry_points={'console_scripts': ['tole=tole.tole_cli:start']},
    author="wetoq",
    description="The simplest way to convert Python scripts to EXE with asset support.",
    long_description="Tole-tool automates PyInstaller to bundle your .py files and all assets (png, mp3, etc.) into a single executable.",
    keywords='python exe tole-tool converter assets',
    url="https://pypi.org/project/tole-tool/", 
)