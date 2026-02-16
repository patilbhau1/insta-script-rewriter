#!/usr/bin/env python3
"""
Setup verification script for Instagram Video Script Rewriter
Run this to check if all dependencies are properly installed
"""

import sys

def check_python_version():
    """Check if Python version is 3.8+"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} - Need 3.8+")
        return False

def check_imports():
    """Check if required packages are installed"""
    packages = {
        'flask': 'Flask',
        'groq': 'Groq API',
        'dotenv': 'python-dotenv',
        'moviepy.editor': 'MoviePy'
    }
    
    all_good = True
    for module, name in packages.items():
        try:
            __import__(module)
            print(f"✓ {name} - installed")
        except ImportError:
            print(f"✗ {name} - NOT installed")
            all_good = False
    
    return all_good

def check_ffmpeg():
    """Check if FFmpeg is available"""
    import subprocess
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, 
                              text=True,
                              timeout=5)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✓ FFmpeg - {version_line}")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("✗ FFmpeg - NOT found (required for video processing)")
        print("  Install: https://ffmpeg.org/download.html")
        return False

def check_env_file():
    """Check if .env file exists and has API key"""
    import os
    from pathlib import Path
    
    env_file = Path('.env')
    if not env_file.exists():
        print("⚠ .env file - NOT found")
        print("  Create from .env.example and add your Groq API key")
        return False
    
    # Load and check for API key
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('GROQ_API_KEY')
    if api_key and api_key != 'your_groq_api_key_here':
        print(f"✓ GROQ_API_KEY - configured ({api_key[:20]}...)")
        return True
    else:
        print("⚠ GROQ_API_KEY - not set or using placeholder")
        print("  Add your actual Groq API key to .env file")
        return False

def check_directories():
    """Check if required directories exist"""
    from pathlib import Path
    
    dirs = ['templates', 'static/css', 'static/js']
    all_good = True
    
    for dir_path in dirs:
        if Path(dir_path).exists():
            print(f"✓ {dir_path}/ - exists")
        else:
            print(f"✗ {dir_path}/ - missing")
            all_good = False
    
    return all_good

def main():
    print("=" * 60)
    print("Instagram Video Script Rewriter - Setup Verification")
    print("=" * 60)
    print()
    
    checks = [
        ("Python Version", check_python_version),
        ("Python Packages", check_imports),
        ("FFmpeg", check_ffmpeg),
        ("Environment Config", check_env_file),
        ("Project Directories", check_directories)
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n{name}:")
        print("-" * 40)
        results.append(check_func())
    
    print("\n" + "=" * 60)
    if all(results):
        print("✓ All checks passed! You're ready to run the application.")
        print("\nStart the server with: python app.py")
        print("Then open: http://localhost:5000")
    else:
        print("⚠ Some checks failed. Please fix the issues above.")
        print("\nRefer to QUICKSTART.md for detailed setup instructions.")
    print("=" * 60)

if __name__ == '__main__':
    main()
