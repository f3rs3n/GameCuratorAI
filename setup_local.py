#!/usr/bin/env python
"""
Setup script for local development of DAT Filter AI.
This script will check for required dependencies and install them if missing.
"""

import sys
import subprocess
import os

def check_module(module_name):
    """Check if a Python module is installed"""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False

def install_module(module_name, package_name=None):
    """Install a Python module using pip"""
    if package_name is None:
        package_name = module_name
    
    print(f"Installing {module_name}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        return True
    except subprocess.CalledProcessError:
        print(f"Error installing {package_name}")
        return False

def main():
    """Main entry point"""
    print("DAT Filter AI - Local Setup")
    print("==========================")
    
    # Check Python version
    py_version = sys.version_info
    print(f"Python version: {py_version.major}.{py_version.minor}.{py_version.micro}")
    
    if py_version.major < 3 or (py_version.major == 3 and py_version.minor < 8):
        print("Warning: Python 3.8 or higher is recommended")
    
    # Create necessary directories
    print("\nCreating required directories...")
    os.makedirs("ToFilter", exist_ok=True)
    os.makedirs("Filtered", exist_ok=True)
    print("Created ToFilter and Filtered directories.")
    
    # Required modules
    modules = [
        ("colorama", "colorama"),
    ]
    
    # AI Provider modules
    optional_modules = [
        ("google.generativeai", "google-generativeai"),
    ]
    
    # Check and install required modules
    print("\nChecking required modules...")
    missing_modules = []
    
    for module_name, package_name in modules:
        if not check_module(module_name):
            missing_modules.append((module_name, package_name))
    
    if missing_modules:
        print("\nThe following required modules are missing:")
        for module_name, package_name in missing_modules:
            print(f"  - {module_name}")
        
        install = input("\nDo you want to install them now? (y/n): ").lower()
        
        if install == 'y':
            for module_name, package_name in missing_modules:
                if not install_module(module_name, package_name):
                    print(f"Warning: Failed to install {module_name}")
        else:
            print("\nPlease install the required modules manually:")
            for _, package_name in missing_modules:
                print(f"  pip install {package_name}")
            print("\nThen run this setup script again.")
            return
    else:
        print("All required modules are installed!")
    
    # Check optional modules
    print("\nChecking optional modules...")
    missing_optional = []
    
    for module_name, package_name in optional_modules:
        if not check_module(module_name):
            missing_optional.append((module_name, package_name))
    
    if missing_optional:
        print("\nThe following optional modules are missing:")
        for module_name, _ in missing_optional:
            print(f"  - {module_name}")
        
        print("\nOptional modules are required for AI-powered filtering:")
        print("  - google.generativeai: Required for Google Gemini filtering")
        print("Note: Without these modules, you can still use the random filter for testing")
        
        install = input("\nDo you want to install them now? (y/n): ").lower()
        
        if install == 'y':
            for module_name, package_name in missing_optional:
                if not install_module(module_name, package_name):
                    print(f"Warning: Failed to install {module_name}")
                    print(f"You can still run the text-based interface without {module_name}")
        else:
            print("\nYou can still run the text-based interface without these modules.")
    else:
        print("All optional modules are installed!")
    
    # Setup complete
    print("\nSetup complete!")
    print("\nTo run DAT Filter AI, you can use:")
    print("  - Interactive text UI: python interactive.py")
    print("  - Headless mode: python headless.py --help")
    
    print("\nPlease place your DAT files in the 'ToFilter' directory")
    print("Filtered results will be saved in the 'Filtered' directory")
    
    print("\nPress Enter to exit...")
    input()

if __name__ == "__main__":
    main()