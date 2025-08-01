#!/usr/bin/env python3
"""
Cleanup script to remove all the generated files
"""

import os
import glob

def cleanup_generated_files():
    """Remove all generated files from previous runs."""
    
    # Files to remove
    files_to_remove = [
        # Generated implementation files
        'implementation_1.py',
        'requirements_3.txt',
        'requirements_4.txt', 
        'test_implementation.py',
        
        # Generated numbered files
        'file_*.txt',
        'file_*.py',
        'main_*.py',
        'main_file.py',
        'main_0.py',
        
        # Test files
        'test_*.py',
        
        # Generated app files
        'app.py',
        'hello.py',
        'joke_cli.py',
        
        # Other common generated files
        'module_*.py',
        'script_*.py'
    ]
    
    removed_count = 0
    
    print("🧹 Cleaning up generated files...")
    
    for pattern in files_to_remove:
        matching_files = glob.glob(pattern)
        for file_path in matching_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"   ❌ Removed: {file_path}")
                    removed_count += 1
            except Exception as e:
                print(f"   ⚠️  Could not remove {file_path}: {e}")
    
    # Remove test directories
    test_dirs = ['tests/', '__pycache__/', '.pytest_cache/']
    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            try:
                import shutil
                shutil.rmtree(test_dir)
                print(f"   ❌ Removed directory: {test_dir}")
                removed_count += 1
            except Exception as e:
                print(f"   ⚠️  Could not remove {test_dir}: {e}")
    
    print(f"\n✅ Cleanup complete! Removed {removed_count} items.")
    print("Ready for a fresh start! 🚀")

if __name__ == "__main__":
    cleanup_generated_files()