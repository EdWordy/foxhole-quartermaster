# build_app.py
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


# ============================================
# Configuration
# ============================================

EXCLUDE_MODULES = [
    'scipy',
    'setuptools',
    'hook',
    'distutils',
    'site',
    'hooks',
    'tornado',
    'PyQt4',
    'PyQt5',
    'pydoc',
    'pythoncom',
    'pytz',
    'pywintypes',
    'sqlite3',
    'pyz',
    'sklearn',
    'scapy',
    'scrapy',
    'sympy',
    'kivy',
    'pyramid',
    'tensorflow',
    'pipenv',
    'pattern',
    'mechanize',
    'beautifulsoup4',
    'requests',
    'wxPython',
    'pygi',
    'pygame',
    'pyglet',
    'flask',
    'django',
    'pylint',
    'pytube',
    'odfpy',
    'mccabe',
    'pilkit',
    'six',
    'wrapt',
    'astroid',
    'isort'
]


def print_status(message, status="INFO"):
    """Print formatted status message."""
    status_colors = {
        "OK": "\033[92m",      # Green
        "ERROR": "\033[91m",   # Red
        "WARNING": "\033[93m", # Yellow
        "INFO": "\033[94m",    # Blue
    }
    reset = "\033[0m"
    
    if platform.system() == "Windows":
        # Windows doesn't support ANSI colors in older terminals
        print(f"[{status}] {message}")
    else:
        color = status_colors.get(status, "")
        print(f"{color}[{status}]{reset} {message}")


def print_section(title):
    """Print section header."""
    print()
    print("=" * 50)
    print(f" {title}")
    print("=" * 50)


# ============================================
# Check Prerequisites
# ============================================

def check_python():
    """Check if Python is properly installed."""
    print_status("Python found", "OK")
    print_status(f"Version: {sys.version.split()[0]}", "INFO")
    return True


def check_pip():
    """Check if pip is installed."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print_status("pip found", "OK")
            return True
        else:
            print_status("pip is not installed or not in PATH", "ERROR")
            return False
    except Exception as e:
        print_status(f"pip check failed: {e}", "ERROR")
        return False


def check_dependencies():
    """Check if required dependencies are installed."""
    print_status("Checking installed packages...", "INFO")
    
    required_packages = {
        'numpy': 'numpy',
        'pandas': 'pandas',
        'matplotlib': 'matplotlib',
        'cv2': 'opencv-python',
        'PIL': 'Pillow',
        'yaml': 'PyYAML',
        'PyInstaller': 'pyinstaller',
        'xlsxwriter': 'xlsxwriter'
    }
    
    missing = []
    for import_name, package_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing.append(package_name)
    
    if missing:
        print_status(f"Missing packages: {', '.join(missing)}", "WARNING")
        return False
    
    print_status("All required packages are installed", "OK")
    return True


# ============================================
# Install Dependencies
# ============================================

def install_dependencies():
    """Install required dependencies."""
    print_status("Installing required packages...", "INFO")
    
    requirements_file = Path("requirements.txt")
    
    if not requirements_file.exists():
        print_status("requirements.txt not found", "ERROR")
        sys.exit(1)
    
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
    )
    
    if result.returncode != 0:
        print_status("Failed to install required packages", "ERROR")
        sys.exit(1)
    
    print_status("Packages installed successfully", "OK")


# ============================================
# Create Build Directories
# ============================================

def create_directories():
    """Create necessary build directories."""
    print_status("Creating build directories...", "INFO")
    
    try:
        os.makedirs("build", exist_ok=True)
        os.makedirs("dist", exist_ok=True)
        print_status("Directories created", "OK")
    except Exception as e:
        print_status(f"Failed to create directories: {e}", "ERROR")
        sys.exit(1)


# ============================================
# Build Executable
# ============================================

def run_pyinstaller():
    """Run PyInstaller to build the executable."""
    print_status("Building executable with PyInstaller...", "INFO")
    
    # Check if spec file exists
    spec_file = Path("foxhole_quartermaster.spec")
    if not spec_file.exists():
        print_status("foxhole_quartermaster.spec file not found", "ERROR")
        sys.exit(1)
    
    # Build PyInstaller command with all exclusions
    cmd = [
        "pyinstaller",
        "--clean",
        "--noconfirm"
    ]
    
    
    # Add spec file
    cmd.append("foxhole_quartermaster.spec")
    
    # Run PyInstaller
    result = subprocess.run(cmd)
    
    if result.returncode != 0:
        print_status("PyInstaller failed to build the executable", "ERROR")
        sys.exit(1)
    
    print_status("Executable built successfully", "OK")


# ============================================
# Copy Additional Files
# ============================================

def copy_additional_files():
    """Copy additional files to the distribution directory."""
    print_status("Copying additional files...", "INFO")
    
    # Define the distribution directory
    dist_dir = Path("dist/FoxholeQuartermaster")
    
    if not dist_dir.exists():
        print_status(f"Distribution directory not found: {dist_dir}", "ERROR")
        sys.exit(1)
    
    # Create data directories
    data_dir = dist_dir / "data"
    processed_templates_dir = data_dir / "processed_templates"
    
    try:
        os.makedirs(processed_templates_dir, exist_ok=True)
    except Exception as e:
        print_status(f"Failed to create data directories: {e}", "WARNING")
    
    # Copy processed templates
    src_templates = Path("data/processed_templates")
    if src_templates.exists():
        try:
            shutil.copytree(src_templates, processed_templates_dir, dirs_exist_ok=True)
            print_status("Processed templates copied", "OK")
        except Exception as e:
            print_status(f"Failed to copy processed templates: {e}", "WARNING")
    else:
        print_status("data/processed_templates not found, skipping", "INFO")
    
    # Copy JSON files
    json_files = [
        ("data/catalog.json", data_dir / "catalog.json"),
        ("data/item_thresholds.json", data_dir / "item_thresholds.json")
    ]
    
    for src, dst in json_files:
        src_path = Path(src)
        if src_path.exists():
            try:
                shutil.copy2(src_path, dst)
                print_status(f"{src_path.name} copied", "OK")
            except Exception as e:
                print_status(f"Failed to copy {src_path.name}: {e}", "WARNING")
        else:
            print_status(f"{src} not found, skipping", "WARNING")
    
    # Copy config file if it exists
    config_file = Path("config.yaml")
    if config_file.exists():
        try:
            shutil.copy2(config_file, dist_dir / "config.yaml")
            print_status("config.yaml copied", "OK")
        except Exception as e:
            print_status(f"Failed to copy config.yaml: {e}", "WARNING")
    else:
        print_status("config.yaml not found, skipping", "INFO")
    
    print_status("Additional files copied", "OK")


# ============================================
# Main Build Function
# ============================================

def main():
    """Main build function."""
    print("===== Foxhole Quartermaster Build Script =====")
    print()
    
    # Check prerequisites
    print_section("Checking Prerequisites")
    check_python()
    if not check_pip():
        sys.exit(1)
    print()
    
    # Check and install dependencies
    print_section("Installing Dependencies")
    if not check_dependencies():
        install_dependencies()
    print()
    
    # Create directories
    print_section("Creating Build Directories")
    create_directories()
    print()
    
    # Run PyInstaller
    print_section("Building Executable")
    run_pyinstaller()
    print()
    
    # Copy additional files
    print_section("Copying Additional Files")
    copy_additional_files()
    print()
    
    # Build complete
    print_section("Build Complete")
    print()
    print("Build completed successfully!")
    print()
    exe_name = "FoxholeQuartermaster.exe" if platform.system() == "Windows" else "FoxholeQuartermaster"
    print(f"Executable location:")
    print(f"  dist/FoxholeQuartermaster/{exe_name}")
    print()
    
    if platform.system() == "Windows":
        input("Press Enter to exit...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_status("\nBuild cancelled by user", "WARNING")
        sys.exit(1)
    except Exception as e:
        print_status(f"Unexpected error: {e}", "ERROR")
        sys.exit(1)