#!/usr/bin/env python3
"""
Build script for Foxhole Quartermaster application.
Creates an executable using PyInstaller.
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import numpy
        import pandas
        import matplotlib
        import cv2
        import PIL
        import yaml
        import PyInstaller
        import xlsxwriter
        print("All required packages are installed.")
        return True
    except ImportError as e:
        print(f"Missing dependency: {e}")
        return False

def install_dependencies():
    """Install required dependencies."""
    print("Installing required packages...")
    requirements_file = Path("requirements.txt")
    
    if not requirements_file.exists():
        print("Creating requirements.txt...")
        with open(requirements_file, "w") as f:
            f.write("""numpy>=1.20.0
pandas>=1.3.0
matplotlib>=3.4.0
opencv-python>=4.5.0
Pillow>=8.0.0
PyYAML>=6.0
pyinstaller>=5.0.0
xlsxwriter>=3.0.0
""")
    
    result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    if result.returncode != 0:
        print("Error: Failed to install required packages")
        sys.exit(1)
    print("All dependencies installed successfully.")

def create_directories():
    """Create necessary build directories."""
    print("Creating build directories...")
    os.makedirs("build", exist_ok=True)
    os.makedirs("dist", exist_ok=True)

def run_pyinstaller():
    """Run PyInstaller to build the executable."""
    print("Building executable with PyInstaller...")
    
    # Check if spec file exists
    spec_file = Path("foxhole_quartermaster.spec")
    if not spec_file.exists():
        print("Error: foxhole_quartermaster.spec file not found")
        sys.exit(1)
    
    # Run PyInstaller
    result = subprocess.run(["pyinstaller", "--clean", "--noconfirm", "foxhole_quartermaster.spec"])
    if result.returncode != 0:
        print("Error: PyInstaller failed to build the executable")
        sys.exit(1)

def copy_additional_files():
    """Copy additional files to the distribution directory."""
    print("Copying additional files...")
    
    # Define the distribution directory
    dist_dir = Path("dist/FoxholeQuartermaster")
    
    # Create CheckImages directory if it doesn't exist
    check_images_dir = dist_dir / "data"
    os.makedirs(check_images_dir, exist_ok=True)
    
    # Copy CheckImages directory
    if Path("data").exists():
        for subdir in ["Default", "Numbers"]:
            src_dir = Path(f"data/{subdir}")
            dst_dir = check_images_dir / subdir
            if src_dir.exists():
                os.makedirs(dst_dir, exist_ok=True)
                for file in src_dir.glob("*.png"):
                    shutil.copy2(file, dst_dir)
    
    # Copy other necessary files
    for file in ["data/catalog.json", "data/item_thresholds.json"]:
        if Path(file).exists():
            shutil.copy2(file, dist_dir)
    
    # Copy config file if it exists
    if Path("config.yaml").exists():
        shutil.copy2("config.yaml", dist_dir)

def main():
    """Main build function."""
    print("===== Foxhole Quartermaster Build Script =====")
    print()
    
    # Check and install dependencies
    if not check_dependencies():
        install_dependencies()
    
    # Create directories
    create_directories()
    
    # Run PyInstaller
    run_pyinstaller()
    
    # Copy additional files
    copy_additional_files()
    
    print()
    print("Build completed successfully!")
    print("Executable is located in dist/FoxholeQuartermaster/FoxholeQuartermaster.exe")
    print()
    
    if platform.system() == "Windows":
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
