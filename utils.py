# Utility functions for the autonomous coding system
import re
from typing import List, Dict, Optional

def extract_code_from_markdown(markdown_text: str) -> List[Dict[str, str]]:
    """
    Extract code blocks from markdown text.
    
    Args:
        markdown_text (str): The markdown text containing code blocks
    
    Returns:
        List[Dict[str, str]]: List of dictionaries with 'language' and 'code' keys
    """
    # Pattern to match code blocks with language specification
    code_block_pattern = r'```(\w+)?\n(.*?)```'
    
    # Pattern to match inline code
    inline_code_pattern = r'`([^`]+)`'
    
    code_blocks = []
    
    # Find code blocks
    for match in re.finditer(code_block_pattern, markdown_text, re.DOTALL):
        language = match.group(1) or 'text'
        code = match.group(2).strip()
        code_blocks.append({
            'language': language,
            'code': code,
            'type': 'block'
        })
    
    # Find inline code
    for match in re.finditer(inline_code_pattern, markdown_text):
        code = match.group(1)
        code_blocks.append({
            'language': 'text',
            'code': code,
            'type': 'inline'
        })
    
    return code_blocks

def extract_python_code(markdown_text: str) -> List[str]:
    """
    Extract only Python code blocks from markdown text.
    
    Args:
        markdown_text (str): The markdown text containing code blocks
    
    Returns:
        List[str]: List of Python code strings
    """
    code_blocks = extract_code_from_markdown(markdown_text)
    python_code = []
    
    for block in code_blocks:
        if block['language'].lower() in ['python', 'py', '']:
            python_code.append(block['code'])
    
    return python_code

def clean_code_string(code: str) -> str:
    """
    Clean and normalize a code string.
    
    Args:
        code (str): The code string to clean
    
    Returns:
        str: Cleaned code string
    """
    # Remove leading/trailing whitespace
    code = code.strip()
    
    # Remove common markdown artifacts
    code = re.sub(r'^```\w*\n', '', code)
    code = re.sub(r'\n```$', '', code)
    
    return code

def validate_python_syntax(code: str) -> Dict[str, any]:
    """
    Validate Python syntax without executing the code.
    
    Args:
        code (str): Python code to validate
    
    Returns:
        Dict[str, any]: Validation results
    """
    try:
        import ast
        ast.parse(code)
        return {
            "valid": True,
            "error": None
        }
    except SyntaxError as e:
        return {
            "valid": False,
            "error": {
                "message": str(e),
                "line": e.lineno,
                "column": e.offset
            }
        }
    except Exception as e:
        return {
            "valid": False,
            "error": {
                "message": f"Unexpected error: {str(e)}",
                "line": None,
                "column": None
            }
        } 