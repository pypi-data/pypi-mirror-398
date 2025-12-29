from setuptools import setup, find_packages

setup(
    name="tole-tool",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "pyinstaller",
    ],
    entry_points={
        'console_scripts': [
            'tole=tole.tole_cli:start',
        ],
    },
    author="Your Name",
    description="CLI tool to convert Python to EXE",
    python_requires='>=3.6',
)