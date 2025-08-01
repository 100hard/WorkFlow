import os
import json
import time
from typing import Dict, Any, List, Optional
from openai import OpenAI


class LLMTool:
    """
    LLM tool for enhanced AI integration.
    Provides methods for interacting with language models.
    """
    
    def __init__(self, api_key: str = None, model: str = "gpt-4", base_url: str = None):
        """
        Initialize the LLM tool.
        
        Args:
            api_key (str): API key (can be a dummy key for local models)
            model (str): Model to use for completions
            base_url (str, optional): The base URL for the LLM API (for Ollama)
        """
        self.api_key = api_key or "ollama" # Default to a dummy key
        self.model = model
        self.base_url = base_url

        # --- FIX: ROBUST CLIENT INITIALIZATION FOR OLLAMA ---
        # This is the most direct way to configure the client. It tells the
        # library to send all requests to your local server and to use the
        # dummy API key, which is exactly what Ollama expects.
        # If a base_url is provided (for Ollama), use it.
        # Otherwise, the client will use the default OpenAI API endpoint.
        self.client = OpenAI(
            base_url=self.base_url, 
            api_key=self.api_key
        )
        
        self.max_retries = 3
        self.retry_delay = 1
    
    def generate_completion(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.1) -> dict:
        """
        Generate a completion using the LLM.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Ollama's response for usage is sometimes None, so we handle that case.
            usage = response.usage
            prompt_tokens = usage.prompt_tokens if usage else 0
            completion_tokens = usage.completion_tokens if usage else 0
            total_tokens = usage.total_tokens if usage else 0

            generated_text = response.choices[0].message.content
            
            return {
                "success": True,
                "text": generated_text,
                "model": self.model,
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to generate completion: {str(e)}",
                "model": self.model
            }
    
    # ... The rest of the methods in this file remain unchanged ...
    def generate_with_retry(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.1) -> dict:
        for attempt in range(self.max_retries):
            result = self.generate_completion(prompt, max_tokens, temperature)
            if result["success"]:
                return result
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay * (attempt + 1))
        return result
    
    def analyze_code(self, code: str, analysis_type: str = "general") -> dict:
        analysis_prompts = {
            "general": f"Analyze the following Python code and provide a comprehensive review:\n\n{code}\n\nPlease provide:\n1. Overall assessment\n2. Potential issues\n3. Suggestions for improvement\n4. Code quality score (1-10)",
            "security": f"Perform a security analysis of the following Python code:\n\n{code}\n\nPlease identify:\n1. Security vulnerabilities\n2. Input validation issues\n3. Potential attack vectors\n4. Security recommendations",
            "performance": f"Analyze the performance characteristics of the following Python code:\n\n{code}\n\nPlease identify:\n1. Performance bottlenecks\n2. Memory usage issues\n3. Optimization opportunities\n4. Performance recommendations",
            "style": f"Review the coding style and conventions of the following Python code:\n\n{code}\n\nPlease check:\n1. PEP 8 compliance\n2. Naming conventions\n3. Code organization\n4. Documentation quality"
        }
        prompt = analysis_prompts.get(analysis_type, analysis_prompts["general"])
        return self.generate_with_retry(prompt, max_tokens=1500)
    
    def generate_tests(self, code: str, test_framework: str = "pytest") -> dict:
        prompt = f"""
        Generate comprehensive {test_framework} tests for the following Python code:
        
        {code}
        
        Please provide:
        1. Unit tests for all functions/methods
        2. Edge case tests
        3. Error handling tests
        4. Integration tests if applicable
        
        Format the tests as executable Python code with proper imports and structure.
        """
        return self.generate_with_retry(prompt, max_tokens=2000)

    def refactor_code(self, code: str, refactoring_type: str = "general") -> dict:
        refactoring_prompts = {
            "general": f"Refactor the following Python code to improve its overall quality:\n\n{code}\n\nPlease provide:\n1. Refactored code\n2. Explanation of changes\n3. Benefits of the refactoring",
            "performance": f"Refactor the following Python code to improve performance:\n\n{code}\n\nPlease provide:\n1. Performance-optimized code\n2. Explanation of optimizations\n3. Expected performance improvements",
            "readability": f"Refactor the following Python code to improve readability:\n\n{code}\n\nPlease provide:\n1. More readable code\n2. Better variable/function names\n3. Improved structure and organization",
            "maintainability": f"Refactor the following Python code to improve maintainability:\n\n{code}\n\nPlease provide:\n1. More maintainable code\n2. Better separation of concerns\n3. Reduced coupling"
        }
        prompt = refactoring_prompts.get(refactoring_type, refactoring_prompts["general"])
        return self.generate_with_retry(prompt, max_tokens=2000)

    def generate_documentation(self, code: str, doc_type: str = "docstring") -> dict:
        doc_prompts = {
            "docstring": f"Generate comprehensive docstrings for the following Python code:\n\n{code}\n\nPlease provide:\n1. Function/method docstrings\n2. Class docstrings\n3. Module docstring\n4. Type hints where applicable",
            "readme": f"Generate a README.md file for the following Python code:\n\n{code}\n\nPlease include:\n1. Project description\n2. Installation instructions\n3. Usage examples\n4. API documentation\n5. Contributing guidelines",
            "api_docs": f"Generate API documentation for the following Python code:\n\n{code}\n\nPlease provide:\n1. Function signatures\n2. Parameter descriptions\n3. Return value descriptions\n4. Usage examples\n5. Error handling information"
        }
        prompt = doc_prompts.get(doc_type, doc_prompts["docstring"])
        return self.generate_with_retry(prompt, max_tokens=2000)

    def debug_code(self, code: str, error_message: str = None) -> dict:
        if error_message:
            prompt = f"Debug the following Python code that produces this error:\n\nCode:\n{code}\n\nError:\n{error_message}\n\nPlease provide:\n1. Root cause analysis\n2. Suggested fixes\n3. Corrected code\n4. Prevention strategies"
        else:
            prompt = f"Analyze the following Python code for potential bugs and issues:\n\n{code}\n\nPlease identify:\n1. Potential bugs\n2. Logic errors\n3. Edge cases\n4. Suggested improvements"
        return self.generate_with_retry(prompt, max_tokens=2000)

    def suggest_improvements(self, code: str, focus_area: str = "general") -> dict:
        improvement_prompts = {
            "general": f"Suggest improvements for the following Python code:\n\n{code}\n\nPlease provide:\n1. Code quality improvements\n2. Best practices recommendations\n3. Modern Python features to use\n4. Architecture suggestions",
            "security": f"Suggest security improvements for the following Python code:\n\n{code}\n\nPlease provide:\n1. Security hardening suggestions\n2. Input validation improvements\n3. Authentication/authorization enhancements\n4. Data protection recommendations",
            "performance": f"Suggest performance improvements for the following Python code:\n\n{code}\n\nPlease provide:\n1. Performance optimization suggestions\n2. Memory usage improvements\n3. Algorithm optimizations\n4. Caching strategies",
            "style": f"Suggest style improvements for the following Python code:\n\n{code}\n\nPlease provide:\n1. PEP 8 compliance suggestions\n2. Naming convention improvements\n3. Code organization recommendations\n4. Documentation enhancements"
        }
        prompt = improvement_prompts.get(focus_area, improvement_prompts["general"])
        return self.generate_with_retry(prompt, max_tokens=1500)

    def get_model_info(self) -> dict:
        return {
            "success": True,
            "model": self.model,
            "api_key_configured": bool(self.api_key),
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay
        }
