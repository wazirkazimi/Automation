"""
Script to clean up unwanted files and organize directory
Run this once to remove old deployment files
"""

import os
import shutil
from pathlib import Path

# Files/directories to keep
KEEP_FILES = {
    '.env',
    '.gitignore',
    '.git',
    '.venv',
    'README.md',
    'requirements.txt',
    'vi.py',
    'config.py',
    'lambda_deployment',
    'uploads',
    'outputs',
    'processed',
    'JScode'
}

# Files/directories to delete
DELETE_PATTERNS = [
    '*.bat',           # start.bat, etc
    '*.sh',            # start.sh, etc
    'test_*.py',       # test files
    'auto.py',
    'exm.py',
    'vid.py',
    'run_stack.py',
    'app.py',          # Old Flask app
    'Dockerfile',      # Old Docker
    'Procfile',        # Old Procfile
    'runtime.txt',
    'DEPLOYMENT*.md',
    'DEPLOYMENT*.txt',
    'GOOGLE_DRIVE*.md',
    'NGROK_SETUP.md',
    'QUICKSTART.md',
    'TROUBLESHOOT*.md',
    'output*.mp4',     # Temp videos
    'output*.png',
    '__pycache__',
]

def clean_directory():
    """Remove unwanted files"""
    root = Path('.')
    
    deleted_count = 0
    
    for pattern in DELETE_PATTERNS:
        for item in root.glob(pattern):
            if item.is_file():
                try:
                    item.unlink()
                    print(f"✓ Deleted: {item}")
                    deleted_count += 1
                except Exception as e:
                    print(f"✗ Failed to delete {item}: {e}")
            elif item.is_dir() and item.name != '.git':
                try:
                    shutil.rmtree(item)
                    print(f"✓ Deleted directory: {item}")
                    deleted_count += 1
                except Exception as e:
                    print(f"✗ Failed to delete {item}: {e}")
    
    print(f"\n✅ Cleanup complete! Deleted {deleted_count} items")
    
    # Show remaining structure
    print("\n📁 Remaining files:")
    for item in sorted(root.iterdir()):
        if item.name.startswith('.'):
            continue
        if item.is_dir():
            print(f"  📂 {item.name}/")
        else:
            print(f"  📄 {item.name}")

if __name__ == '__main__':
    print("🧹 Cleaning up unwanted files...\n")
    clean_directory()
