# File system operations for the autonomous coding system
import os
import json
import shutil
from typing import Optional, List, Dict, Any
from pathlib import Path

def save_file(file_path: str, content: str, overwrite: bool = True) -> dict:
    """
    Save content to a file.
    
    Args:
        file_path (str): Path to the file
        content (str): Content to save
        overwrite (bool): Whether to overwrite existing file
        
    Returns:
        dict: Result with success status and details
    """
    try:
        # Create directory if it doesn't exist
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        
        # Check if file exists and overwrite setting
        if os.path.exists(file_path) and not overwrite:
            return {
                "success": False,
                "error": f"File {file_path} already exists and overwrite=False"
            }
        
        # Write content to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {
            "success": True,
            "file_path": file_path,
            "size": len(content),
            "message": f"File saved successfully: {file_path}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to save file {file_path}: {str(e)}"
        }

def read_file(file_path: str) -> dict:
    """
    Read content from a file.
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        dict: Result with success status and content
    """
    try:
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"File {file_path} does not exist"
            }
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "success": True,
            "content": content,
            "file_path": file_path,
            "size": len(content)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to read file {file_path}: {str(e)}"
        }

def list_files(directory: str = ".", pattern: str = "*") -> dict:
    """
    List files in a directory with optional pattern matching.
    
    Args:
        directory (str): Directory to list
        pattern (str): File pattern to match
        
    Returns:
        dict: Result with success status and file list
    """
    try:
        if not os.path.exists(directory):
            return {
                "success": False,
                "error": f"Directory {directory} does not exist"
            }
        
        files = []
        for file_path in Path(directory).glob(pattern):
            if file_path.is_file():
                stat = file_path.stat()
                files.append({
                    "name": file_path.name,
                    "path": str(file_path),
                    "size": stat.st_size,
                    "modified": stat.st_mtime
                })
        
        return {
            "success": True,
            "files": files,
            "count": len(files),
            "directory": directory
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to list files in {directory}: {str(e)}"
        }

def create_directory(directory_path: str) -> dict:
    """
    Create a directory and its parent directories if needed.
    
    Args:
        directory_path (str): Path to create
        
    Returns:
        dict: Result with success status
    """
    try:
        os.makedirs(directory_path, exist_ok=True)
        
        return {
            "success": True,
            "directory_path": directory_path,
            "message": f"Directory created successfully: {directory_path}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to create directory {directory_path}: {str(e)}"
        }

def delete_file(file_path: str) -> dict:
    """
    Delete a file.
    
    Args:
        file_path (str): Path to the file to delete
        
    Returns:
        dict: Result with success status
    """
    try:
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"File {file_path} does not exist"
            }
        
        os.remove(file_path)
        
        return {
            "success": True,
            "file_path": file_path,
            "message": f"File deleted successfully: {file_path}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to delete file {file_path}: {str(e)}"
        }

def copy_file(source_path: str, destination_path: str) -> dict:
    """
    Copy a file from source to destination.
    
    Args:
        source_path (str): Source file path
        destination_path (str): Destination file path
        
    Returns:
        dict: Result with success status
    """
    try:
        if not os.path.exists(source_path):
            return {
                "success": False,
                "error": f"Source file {source_path} does not exist"
            }
        
        # Create destination directory if it doesn't exist
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        
        shutil.copy2(source_path, destination_path)
        
        return {
            "success": True,
            "source_path": source_path,
            "destination_path": destination_path,
            "message": f"File copied successfully: {source_path} -> {destination_path}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to copy file {source_path}: {str(e)}"
        }

def get_file_info(file_path: str) -> dict:
    """
    Get detailed information about a file.
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        dict: Result with success status and file info
    """
    try:
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"File {file_path} does not exist"
            }
        
        stat = os.stat(file_path)
        
        return {
            "success": True,
            "file_path": file_path,
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "created": stat.st_ctime,
            "is_file": os.path.isfile(file_path),
            "is_directory": os.path.isdir(file_path),
            "permissions": oct(stat.st_mode)[-3:]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get file info for {file_path}: {str(e)}"
        }

def search_files(directory: str, pattern: str, recursive: bool = True) -> dict:
    """
    Search for files matching a pattern.
    
    Args:
        directory (str): Directory to search
        pattern (str): Pattern to match (supports glob patterns)
        recursive (bool): Whether to search recursively
        
    Returns:
        dict: Result with success status and matching files
    """
    try:
        if not os.path.exists(directory):
            return {
                "success": False,
                "error": f"Directory {directory} does not exist"
            }
        
        matches = []
        search_path = Path(directory)
        
        if recursive:
            glob_pattern = f"**/{pattern}"
        else:
            glob_pattern = pattern
        
        for file_path in search_path.glob(glob_pattern):
            if file_path.is_file():
                stat = file_path.stat()
                matches.append({
                    "name": file_path.name,
                    "path": str(file_path),
                    "relative_path": str(file_path.relative_to(search_path)),
                    "size": stat.st_size,
                    "modified": stat.st_mtime
                })
        
        return {
            "success": True,
            "matches": matches,
            "count": len(matches),
            "directory": directory,
            "pattern": pattern
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to search files in {directory}: {str(e)}"
        }

def save_json(file_path: str, data: dict, indent: int = 2) -> dict:
    """
    Save data as JSON file.
    
    Args:
        file_path (str): Path to the JSON file
        data (dict): Data to save
        indent (int): JSON indentation
        
    Returns:
        dict: Result with success status
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        
        return {
            "success": True,
            "file_path": file_path,
            "message": f"JSON file saved successfully: {file_path}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to save JSON file {file_path}: {str(e)}"
        }

def read_json(file_path: str) -> dict:
    """
    Read data from JSON file.
    
    Args:
        file_path (str): Path to the JSON file
        
    Returns:
        dict: Result with success status and data
    """
    try:
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"JSON file {file_path} does not exist"
            }
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return {
            "success": True,
            "data": data,
            "file_path": file_path
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to read JSON file {file_path}: {str(e)}"
        } 