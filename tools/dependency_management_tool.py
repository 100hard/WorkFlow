# Dependency management tools for the autonomous coding system
import subprocess
import re
import os
import json
from typing import List, Dict, Optional, Any
from pathlib import Path

def add_dependency_to_requirements(library_name: str, version: str = None) -> dict:
    """
    Add a dependency to requirements.txt file.
    
    Args:
        library_name (str): Name of the library to add
        version (str): Version specification (optional)
        
    Returns:
        dict: Result with success status
    """
    try:
        requirements_file = "requirements.txt"
        
        # Read existing requirements
        existing_requirements = []
        if os.path.exists(requirements_file):
            with open(requirements_file, 'r') as f:
                existing_requirements = [line.strip() for line in f.readlines() if line.strip()]
        
        # Check if library already exists
        for req in existing_requirements:
            if req.split('==')[0].split('>=')[0].split('<=')[0].strip() == library_name:
                return {
                    "success": False,
                    "error": f"Library {library_name} already exists in requirements.txt"
                }
        
        # Create new requirement line
        if version:
            new_requirement = f"{library_name}=={version}"
        else:
            new_requirement = library_name
        
        # Add to requirements
        existing_requirements.append(new_requirement)
        
        # Write back to file
        with open(requirements_file, 'w') as f:
            f.write('\n'.join(existing_requirements) + '\n')
        
        return {
            "success": True,
            "library": library_name,
            "version": version,
            "requirement": new_requirement,
            "message": f"Added {new_requirement} to requirements.txt"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to add dependency {library_name}: {str(e)}"
        }

def remove_dependency_from_requirements(library_name: str) -> dict:
    """
    Remove a dependency from requirements.txt file.
    
    Args:
        library_name (str): Name of the library to remove
        
    Returns:
        dict: Result with success status
    """
    try:
        requirements_file = "requirements.txt"
        
        if not os.path.exists(requirements_file):
            return {
                "success": False,
                "error": "requirements.txt file does not exist"
            }
        
        # Read existing requirements
        with open(requirements_file, 'r') as f:
            requirements = f.readlines()
        
        # Filter out the library to remove
        filtered_requirements = []
        removed = False
        
        for line in requirements:
            line_stripped = line.strip()
            if line_stripped:
                library_part = line_stripped.split('==')[0].split('>=')[0].split('<=')[0].strip()
                if library_part != library_name:
                    filtered_requirements.append(line)
                else:
                    removed = True
        
        if not removed:
            return {
                "success": False,
                "error": f"Library {library_name} not found in requirements.txt"
            }
        
        # Write back to file
        with open(requirements_file, 'w') as f:
            f.writelines(filtered_requirements)
        
        return {
            "success": True,
            "library": library_name,
            "message": f"Removed {library_name} from requirements.txt"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to remove dependency {library_name}: {str(e)}"
        }

def update_dependency_version(library_name: str, new_version: str) -> dict:
    """
    Update the version of a dependency in requirements.txt.
    
    Args:
        library_name (str): Name of the library to update
        new_version (str): New version specification
        
    Returns:
        dict: Result with success status
    """
    try:
        requirements_file = "requirements.txt"
        
        if not os.path.exists(requirements_file):
            return {
                "success": False,
                "error": "requirements.txt file does not exist"
            }
        
        # Read existing requirements
        with open(requirements_file, 'r') as f:
            requirements = f.readlines()
        
        # Update the specific library
        updated_requirements = []
        updated = False
        
        for line in requirements:
            line_stripped = line.strip()
            if line_stripped:
                library_part = line_stripped.split('==')[0].split('>=')[0].split('<=')[0].strip()
                if library_part == library_name:
                    updated_requirements.append(f"{library_name}=={new_version}\n")
                    updated = True
                else:
                    updated_requirements.append(line)
            else:
                updated_requirements.append(line)
        
        if not updated:
            return {
                "success": False,
                "error": f"Library {library_name} not found in requirements.txt"
            }
        
        # Write back to file
        with open(requirements_file, 'w') as f:
            f.writelines(updated_requirements)
        
        return {
            "success": True,
            "library": library_name,
            "new_version": new_version,
            "message": f"Updated {library_name} to version {new_version}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to update dependency {library_name}: {str(e)}"
        }

def parse_requirements_file(requirements_file: str = "requirements.txt") -> dict:
    """
    Parse a requirements.txt file and return dependency information.
    
    Args:
        requirements_file (str): Path to requirements.txt file
        
    Returns:
        dict: Result with success status and dependency list
    """
    try:
        if not os.path.exists(requirements_file):
            return {
                "success": False,
                "error": f"Requirements file {requirements_file} does not exist"
            }
        
        dependencies = []
        
        with open(requirements_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Parse dependency line
                try:
                    if '==' in line:
                        name, version = line.split('==', 1)
                        constraint = '=='
                    elif '>=' in line:
                        name, version = line.split('>=', 1)
                        constraint = '>='
                    elif '<=' in line:
                        name, version = line.split('<=', 1)
                        constraint = '<='
                    elif '>' in line:
                        name, version = line.split('>', 1)
                        constraint = '>'
                    elif '<' in line:
                        name, version = line.split('<', 1)
                        constraint = '<'
                    else:
                        name = line
                        version = None
                        constraint = None
                    
                    dependencies.append({
                        "name": name.strip(),
                        "version": version.strip() if version else None,
                        "constraint": constraint,
                        "line_number": line_num,
                        "original_line": line
                    })
                    
                except Exception as e:
                    # Skip malformed lines
                    continue
        
        return {
            "success": True,
            "dependencies": dependencies,
            "count": len(dependencies),
            "file_path": requirements_file
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to parse requirements file: {str(e)}"
        }

def check_dependency_conflicts(requirements_file: str = "requirements.txt") -> dict:
    """
    Check for potential dependency conflicts in requirements.txt.
    
    Args:
        requirements_file (str): Path to requirements.txt file
        
    Returns:
        dict: Result with success status and conflict information
    """
    try:
        # Parse requirements
        parse_result = parse_requirements_file(requirements_file)
        if not parse_result["success"]:
            return parse_result
        
        dependencies = parse_result["dependencies"]
        conflicts = []
        
        # Check for duplicate packages
        package_names = [dep["name"] for dep in dependencies]
        duplicates = [name for name in set(package_names) if package_names.count(name) > 1]
        
        for duplicate in duplicates:
            duplicate_deps = [dep for dep in dependencies if dep["name"] == duplicate]
            conflicts.append({
                "type": "duplicate",
                "package": duplicate,
                "entries": duplicate_deps,
                "message": f"Package {duplicate} appears multiple times"
            })
        
        # Check for version conflicts (simplified)
        for i, dep1 in enumerate(dependencies):
            for j, dep2 in enumerate(dependencies[i+1:], i+1):
                if dep1["name"] == dep2["name"] and dep1["version"] != dep2["version"]:
                    conflicts.append({
                        "type": "version_conflict",
                        "package": dep1["name"],
                        "versions": [dep1["version"], dep2["version"]],
                        "entries": [dep1, dep2],
                        "message": f"Version conflict for {dep1['name']}: {dep1['version']} vs {dep2['version']}"
                    })
        
        return {
            "success": True,
            "conflicts": conflicts,
            "conflict_count": len(conflicts),
            "dependencies": dependencies,
            "file_path": requirements_file
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to check dependency conflicts: {str(e)}"
        }

def install_requirements(requirements_file: str = "requirements.txt", upgrade: bool = False) -> dict:
    """
    Install dependencies from requirements.txt.
    
    Args:
        requirements_file (str): Path to requirements.txt file
        upgrade (bool): Whether to upgrade existing packages
        
    Returns:
        dict: Result with success status
    """
    try:
        if not os.path.exists(requirements_file):
            return {
                "success": False,
                "error": f"Requirements file {requirements_file} does not exist"
            }
        
        # Build pip command
        cmd_parts = ["pip", "install", "-r", requirements_file]
        
        if upgrade:
            cmd_parts.append("--upgrade")
        
        command = " ".join(cmd_parts)
        
        # Execute command
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        return {
            "success": result.returncode == 0,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "command": command,
            "requirements_file": requirements_file
        }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Installation timed out after 10 minutes",
            "requirements_file": requirements_file
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to install requirements: {str(e)}",
            "requirements_file": requirements_file
        }

def create_requirements_from_imports(project_path: str = ".", output_file: str = "requirements.txt") -> dict:
    """
    Create requirements.txt from Python imports in a project.
    
    Args:
        project_path (str): Path to the project directory
        output_file (str): Output requirements.txt file
        
    Returns:
        dict: Result with success status
    """
    try:
        if not os.path.exists(project_path):
            return {
                "success": False,
                "error": f"Project path {project_path} does not exist"
            }
        
        # Find all Python files
        python_files = []
        for root, dirs, files in os.walk(project_path):
            # Skip virtual environments and common directories
            dirs[:] = [d for d in dirs if d not in ['venv', 'env', '__pycache__', '.git']]
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        
        # Extract imports
        imports = set()
        import_pattern = re.compile(r'^(?:from\s+(\w+(?:\.\w+)*)\s+import|import\s+(\w+(?:\.\w+)*))')
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            match = import_pattern.match(line)
                            if match:
                                module = match.group(1) or match.group(2)
                                if module:
                                    # Get the top-level package
                                    top_level = module.split('.')[0]
                                    imports.add(top_level)
            except Exception:
                continue
        
        # Filter out standard library modules
        stdlib_modules = {
            'os', 'sys', 're', 'json', 'time', 'datetime', 'pathlib', 'subprocess',
            'typing', 'collections', 'itertools', 'functools', 'argparse', 'logging'
        }
        
        external_imports = imports - stdlib_modules
        
        # Write requirements.txt
        with open(output_file, 'w') as f:
            for import_name in sorted(external_imports):
                f.write(f"{import_name}\n")
        
        return {
            "success": True,
            "imports": list(external_imports),
            "import_count": len(external_imports),
            "output_file": output_file,
            "message": f"Created requirements.txt with {len(external_imports)} external dependencies"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to create requirements from imports: {str(e)}"
        }

def validate_requirements_format(requirements_file: str = "requirements.txt") -> dict:
    """
    Validate the format of requirements.txt file.
    
    Args:
        requirements_file (str): Path to requirements.txt file
        
    Returns:
        dict: Result with success status and validation results
    """
    try:
        if not os.path.exists(requirements_file):
            return {
                "success": False,
                "error": f"Requirements file {requirements_file} does not exist"
            }
        
        parse_result = parse_requirements_file(requirements_file)
        if not parse_result["success"]:
            return parse_result
        
        dependencies = parse_result["dependencies"]
        errors = []
        warnings = []
        
        for dep in dependencies:
            # Check for invalid package names
            if not re.match(r'^[a-zA-Z0-9_-]+$', dep["name"]):
                errors.append(f"Invalid package name: {dep['name']}")
            
            # Check for version format
            if dep["version"]:
                if not re.match(r'^[0-9]+\.[0-9]+(\.[0-9]+)?(a|b|rc)?[0-9]*$', dep["version"]):
                    warnings.append(f"Unusual version format: {dep['name']}=={dep['version']}")
        
        return {
            "success": True,
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "dependencies": dependencies,
            "file_path": requirements_file
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to validate requirements format: {str(e)}"
        } 