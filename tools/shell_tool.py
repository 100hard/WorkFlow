# Shell execution tools for the autonomous coding system
import subprocess
import sys
import os
import platform
import time
from typing import List, Dict, Optional, Any
from pathlib import Path

def execute_command(command: str, cwd: str = None, timeout: int = 300) -> dict:
    """
    Execute a shell command and return the result.
    
    Args:
        command (str): Command to execute
        cwd (str): Working directory for the command
        timeout (int): Timeout in seconds
        
    Returns:
        dict: Result with success status and output
    """
    try:
        # Set up the process
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=cwd
        )
        
        # Execute with timeout
        stdout, stderr = process.communicate(timeout=timeout)
        return_code = process.returncode
        
        return {
            "success": return_code == 0,
            "return_code": return_code,
            "stdout": stdout,
            "stderr": stderr,
            "command": command,
            "cwd": cwd or os.getcwd()
        }
        
    except subprocess.TimeoutExpired:
        process.kill()
        return {
            "success": False,
            "error": f"Command timed out after {timeout} seconds",
            "command": command,
            "cwd": cwd or os.getcwd()
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to execute command: {str(e)}",
            "command": command,
            "cwd": cwd or os.getcwd()
        }

def execute_pytest(test_path: str = ".", verbose: bool = True) -> dict:
    """
    Execute pytest on the specified path.
    
    Args:
        test_path (str): Path to test files or directory
        verbose (bool): Whether to run in verbose mode
        
    Returns:
        dict: Result with success status and test results
    """
    try:
        # Build pytest command
        cmd_parts = ["python", "-m", "pytest"]
        
        if verbose:
            cmd_parts.append("-v")
        
        cmd_parts.append(test_path)
        
        command = " ".join(cmd_parts)
        
        # Execute pytest
        result = execute_command(command)
        
        # Parse test results
        if result["success"]:
            # Extract test statistics from stdout
            stdout = result["stdout"]
            test_stats = {
                "passed": 0,
                "failed": 0,
                "errors": 0,
                "skipped": 0
            }
            
            # Simple parsing of pytest output
            for line in stdout.split('\n'):
                if "passed" in line and "failed" in line:
                    # Look for summary line
                    parts = line.split()
                    for part in parts:
                        if "passed" in part:
                            test_stats["passed"] = int(part.split('passed')[0])
                        elif "failed" in part:
                            test_stats["failed"] = int(part.split('failed')[0])
                        elif "error" in part:
                            test_stats["errors"] = int(part.split('error')[0])
                        elif "skipped" in part:
                            test_stats["skipped"] = int(part.split('skipped')[0])
            
            result["test_stats"] = test_stats
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to execute pytest: {str(e)}",
            "test_path": test_path
        }

def install_package(package_name: str, version: str = None) -> dict:
    """
    Install a Python package using pip.
    
    Args:
        package_name (str): Name of the package to install
        version (str): Specific version to install
        
    Returns:
        dict: Result with success status
    """
    try:
        # Build pip command
        if version:
            package_spec = f"{package_name}=={version}"
        else:
            package_spec = package_name
        
        command = f"pip install {package_spec}"
        
        result = execute_command(command)
        
        if result["success"]:
            result["message"] = f"Package {package_spec} installed successfully"
        else:
            result["error"] = f"Failed to install package {package_spec}: {result.get('stderr', 'Unknown error')}"
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to install package {package_name}: {str(e)}"
        }

def uninstall_package(package_name: str) -> dict:
    """
    Uninstall a Python package using pip.
    
    Args:
        package_name (str): Name of the package to uninstall
        
    Returns:
        dict: Result with success status
    """
    try:
        command = f"pip uninstall {package_name} -y"
        
        result = execute_command(command)
        
        if result["success"]:
            result["message"] = f"Package {package_name} uninstalled successfully"
        else:
            result["error"] = f"Failed to uninstall package {package_name}: {result.get('stderr', 'Unknown error')}"
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to uninstall package {package_name}: {str(e)}"
        }

def list_installed_packages() -> dict:
    """
    List installed Python packages.
    
    Returns:
        dict: Result with success status and package list
    """
    try:
        command = "pip list"
        
        result = execute_command(command)
        
        if result["success"]:
            # Parse package list
            packages = []
            lines = result["stdout"].strip().split('\n')[2:]  # Skip header lines
            
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        packages.append({
                            "name": parts[0],
                            "version": parts[1]
                        })
            
            result["packages"] = packages
            result["count"] = len(packages)
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to list installed packages: {str(e)}"
        }

def run_python_script(script_path: str, args: List[str] = None, cwd: str = None) -> dict:
    """
    Run a Python script.
    
    Args:
        script_path (str): Path to the Python script
        args (List[str]): Command line arguments
        cwd (str): Working directory
        
    Returns:
        dict: Result with success status and output
    """
    try:
        if not os.path.exists(script_path):
            return {
                "success": False,
                "error": f"Script {script_path} does not exist"
            }
        
        # Build command
        cmd_parts = ["python", script_path]
        if args:
            cmd_parts.extend(args)
        
        command = " ".join(cmd_parts)
        
        result = execute_command(command, cwd=cwd)
        result["script_path"] = script_path
        result["args"] = args
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to run Python script {script_path}: {str(e)}"
        }

def check_python_syntax(file_path: str) -> dict:
    """
    Check Python syntax of a file.
    
    Args:
        file_path (str): Path to the Python file
        
    Returns:
        dict: Result with success status
    """
    try:
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"File {file_path} does not exist"
            }
        
        command = f"python -m py_compile {file_path}"
        
        result = execute_command(command)
        result["file_path"] = file_path
        
        if result["success"]:
            result["message"] = f"Syntax check passed for {file_path}"
        else:
            result["error"] = f"Syntax errors in {file_path}: {result.get('stderr', 'Unknown error')}"
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to check syntax for {file_path}: {str(e)}"
        }

def get_system_info() -> dict:
    """
    Get system information.
    
    Returns:
        dict: System information
    """
    try:
        info = {
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": sys.version,
            "python_executable": sys.executable,
            "current_directory": os.getcwd()
        }
        
        return {
            "success": True,
            "system_info": info
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get system info: {str(e)}"
        }

def create_virtual_environment(venv_path: str, python_version: str = None) -> dict:
    """
    Create a Python virtual environment.
    
    Args:
        venv_path (str): Path for the virtual environment
        python_version (str): Python version to use
        
    Returns:
        dict: Result with success status
    """
    try:
        # Build venv command
        if python_version:
            command = f"python{python_version} -m venv {venv_path}"
        else:
            command = f"python -m venv {venv_path}"
        
        result = execute_command(command)
        
        if result["success"]:
            result["message"] = f"Virtual environment created successfully at {venv_path}"
            result["venv_path"] = venv_path
        else:
            result["error"] = f"Failed to create virtual environment: {result.get('stderr', 'Unknown error')}"
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to create virtual environment: {str(e)}"
        }

def activate_virtual_environment(venv_path: str) -> dict:
    """
    Activate a Python virtual environment.
    
    Args:
        venv_path (str): Path to the virtual environment
        
    Returns:
        dict: Result with success status
    """
    try:
        if not os.path.exists(venv_path):
            return {
                "success": False,
                "error": f"Virtual environment {venv_path} does not exist"
            }
        
        # Determine activation script path
        if platform.system() == "Windows":
            activate_script = os.path.join(venv_path, "Scripts", "activate.bat")
        else:
            activate_script = os.path.join(venv_path, "bin", "activate")
        
        if not os.path.exists(activate_script):
            return {
                "success": False,
                "error": f"Activation script not found: {activate_script}"
            }
        
        # Note: This is a simplified version. In practice, you'd need to
        # modify the current process environment or use a subprocess
        return {
            "success": True,
            "message": f"Virtual environment activation script found: {activate_script}",
            "activate_script": activate_script,
            "venv_path": venv_path
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to activate virtual environment: {str(e)}"
        }

def run_git_command(command: str, cwd: str = None) -> dict:
    """
    Run a git command.
    
    Args:
        command (str): Git command to run
        cwd (str): Working directory
        
    Returns:
        dict: Result with success status and output
    """
    try:
        # Ensure it's a git command
        if not command.startswith("git "):
            command = f"git {command}"
        
        result = execute_command(command, cwd=cwd)
        result["git_command"] = command
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to run git command: {str(e)}",
            "git_command": command
        } 