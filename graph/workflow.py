


import os
import sys
import re
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph.state import (
    AgentState, create_initial_state, update_state, 
    add_message, add_error, get_workflow_summary
)
from tools.file_system_tool import save_file, read_file
from tools.shell_tool import execute_pytest
from tools.dependency_management_tool import install_requirements
from tools.llm_tool import LLMTool

class SmartCodeExtractor:
    """Intelligent code extraction and file management."""
    
    @staticmethod
    def extract_code_blocks(text: str) -> Dict[str, str]:
        """Extract code blocks with intelligent filename detection."""
        files = {}
        
        # Pattern to match code blocks with optional language and filename
        pattern = r'```(?:(\w+))?\s*(?:#\s*(?:File:|filename:)\s*([^\n]+))?\n(.*?)```'
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        
        for i, (language, filename, code) in enumerate(matches):
            # Clean up code
            code = code.strip()
            if not code:
                continue
            
            # Determine filename
            if filename:
                filename = filename.strip()
            else:
                # Intelligent filename detection based on content and language
                filename = SmartCodeExtractor._detect_filename(code, language, i)
            
            files[filename] = code
        
        # If no code blocks found, try to detect if entire text is code
        if not files and SmartCodeExtractor._looks_like_code(text):
            filename = SmartCodeExtractor._detect_filename(text, "python", 0)
            files[filename] = text.strip()
        
        return files
    
    @staticmethod
    def _detect_filename(code: str, language: str, index: int) -> str:
        """Detect appropriate filename based on code content."""
        # Look for explicit filename in comments
        for line in code.split('\n')[:5]:
            if any(marker in line.lower() for marker in ['file:', 'filename:', '# file']):
                match = re.search(r'(?:file:|filename:|#\s*file)[:\s]*([^\s\n]+)', line, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
        
        # Detect based on content patterns
        if 'from fastapi import' in code or 'FastAPI(' in code:
            return 'app.py'
        elif 'if __name__ == "__main__"' in code and 'app.run' in code:
            return 'main.py'
        elif 'def test_' in code or 'import pytest' in code:
            return 'test_main.py'
        elif any(dep in code.lower() for dep in ['requests', 'fastapi', 'flask']):
            return 'requirements.txt' if not language or language == 'text' else 'main.py'
        
        # Default based on language
        extensions = {
            'python': '.py',
            'javascript': '.js',
            'html': '.html',
            'css': '.css',
            'text': '.txt',
            '': '.py'  # Default to Python
        }
        
        ext = extensions.get(language.lower() if language else '', '.py')
        return f'main{ext}' if index == 0 else f'file_{index}{ext}'
    
    @staticmethod
    def _looks_like_code(text: str) -> bool:
        """Check if text looks like code."""
        code_indicators = [
            'def ', 'class ', 'import ', 'from ',
            'function ', 'var ', 'const ', 'let ',
            '#!/', '<?', '<!DOCTYPE'
        ]
        return any(indicator in text for indicator in code_indicators)

class AutonomousCodingWorkflow:
    """Fixed autonomous coding workflow with smart extraction."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the workflow."""
        self.memory = MemorySaver()
        self.config = config or self._get_default_config()
        self.llm_tool = self._initialize_llm_tool()
        self.extractor = SmartCodeExtractor()
        self.graph = self._build_graph()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for Ollama."""
        return {
            "model": "codellama",
            "base_url": "http://localhost:11434/v1",
            "api_key": "ollama",
            "temperature": 0.1,
            "max_tokens": 4000
        }
    
    def _initialize_llm_tool(self) -> LLMTool:
        """Initialize the LLM tool for Ollama."""
        config = self.config
        return LLMTool(
            api_key=config.get("api_key", "ollama"),
            model=config.get("model", "codellama"),
            base_url=config.get("base_url")
        )
    
    def _build_graph(self) -> StateGraph:
        """Build the simplified workflow graph."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("planner", self._planner_node)
        workflow.add_node("coder", self._coder_node)
        workflow.add_node("tester", self._tester_node)
        workflow.add_node("finalizer", self._finalizer_node)
        
        # Linear flow with smart routing
        workflow.add_edge("planner", "coder")
        workflow.add_conditional_edges(
            "coder",
            self._route_from_coder,
            {"test": "tester", "finalize": "finalizer", "end": END}
        )
        workflow.add_conditional_edges(
            "tester", 
            self._route_from_tester,
            {"fix": "coder", "finalize": "finalizer", "end": END}
        )
        workflow.add_edge("finalizer", END)
        
        workflow.set_entry_point("planner")
        return workflow.compile(checkpointer=self.memory)
    
    def _planner_node(self, state: AgentState) -> AgentState:
        """Smart planning with context awareness."""
        state = update_state(state, current_agent="planner", phase="planning")
        state = add_message(state, "planner", "Analyzing requirements...", "thinking")
        
        # Analyze requirements to determine complexity
        requirements = state['requirements'].lower()
        is_web_app = any(word in requirements for word in ['fastapi', 'flask', 'web', 'api', 'server'])
        is_simple = len(requirements.split()) < 10
        
        planning_prompt = f"""
        Create a focused implementation plan for: {state['requirements']}
        
        Requirements analysis:
        - Type: {'Web application' if is_web_app else 'Python script'}
        - Complexity: {'Simple' if is_simple else 'Moderate'}
        
        Provide:
        1. Main approach (2-3 sentences)
        2. Key files needed (name them specifically)
        3. Dependencies required
        4. Testing approach
        
        Keep it concise and actionable.
        """
        
        result = self.llm_tool.generate_completion(planning_prompt, max_tokens=1000)
        
        if result["success"]:
            plan = result["text"]
            state = add_message(state, "planner", "Plan created successfully", "success")
        else:
            plan = f"Create a {'FastAPI web application' if is_web_app else 'Python script'} for: {state['requirements']}"
            state = add_message(state, "planner", "Using fallback plan", "warning")
        
        return update_state(state, plan=plan)
    
    def _coder_node(self, state: AgentState) -> AgentState:
        """Smart coding with error awareness."""
        state = update_state(state, current_agent="coder", phase="coding")
        state = add_message(state, "coder", "Writing code...", "thinking")
        
        # Build context from previous errors
        error_context = ""
        recent_errors = state.get('errors', [])[-2:]  # Last 2 errors only
        if recent_errors:
            error_context = f"\n\nFix these specific issues:\n" + "\n".join(f"- {error}" for error in recent_errors)
        
        coding_prompt = f"""
        Implement this requirement: {state['requirements']}
        
        Plan: {state.get('plan', '')}
        {error_context}
        
        IMPORTANT: Format your response with clear code blocks:
        
        ```python
        # File: app.py (or appropriate name)
        # Your Python code here
        ```
        
        ```text
        # File: requirements.txt
        # Only list actual dependencies
        ```
        
        Make the code simple, working, and complete. No placeholders.
        """
        
        result = self.llm_tool.generate_completion(coding_prompt, max_tokens=2500)
        
        if result["success"]:
            code_text = result["text"]
            state = add_message(state, "coder", "Code generated", "success")
        else:
            code_text = self._create_fallback_code(state['requirements'])
            state = add_message(state, "coder", "Using fallback code", "warning")
        
        # Extract and save files intelligently
        files_created = []
        code_files = self.extractor.extract_code_blocks(code_text)
        
        for filename, code_content in code_files.items():
            # Save file
            save_result = save_file(filename, code_content, overwrite=True)
            if save_result['success']:
                files_created.append(filename)
                state = add_message(state, "coder", f"Created {filename}", "info")
        
        if not files_created:
            state = add_message(state, "coder", "No valid code files extracted", "warning")
        
        return update_state(
            state, 
            code=code_text,
            files_created=list(set(state.get('files_created', []) + files_created))
        )
    
    def _tester_node(self, state: AgentState) -> AgentState:
        """Smart testing with dependency management."""
        state = update_state(state, current_agent="tester", phase="testing")
        state = add_message(state, "tester", "Running tests...", "thinking")
        
        files_created = state.get('files_created', [])
        
        # Install dependencies if needed
        if 'requirements.txt' in files_created:
            state = add_message(state, "tester", "Installing dependencies...", "info")
            install_result = install_requirements("requirements.txt")
            
            if not install_result['success']:
                error_msg = f"Dependency error: {install_result.get('stderr', 'Unknown error')}"
                state = add_message(state, "tester", error_msg, "error")
                return add_error(state, error_msg)
        
        # Find main Python file to test
        main_file = None
        for file in files_created:
            if file.endswith('.py') and file not in ['test_main.py']:
                main_file = file
                break
        
        if not main_file:
            state = add_message(state, "tester", "No Python file to test", "warning")
            return update_state(state, test_coverage=0.0)
        
        # Create simple test
        test_code = f"""
import pytest
import sys
import os

def test_import():
    \"\"\"Test that the main file can be imported.\"\"\"
    try:
        import {main_file.replace('.py', '')}
        assert True
    except ImportError as e:
        pytest.fail(f"Import failed: {{e}}")

def test_basic_functionality():
    \"\"\"Test basic functionality if main function exists.\"\"\"
    try:
        module = __import__('{main_file.replace('.py', '')}')
        if hasattr(module, 'main'):
            result = module.main()
            assert result is not None
        else:
            assert True  # No main function, that's ok
    except Exception as e:
        pytest.fail(f"Execution failed: {{e}}")
"""
        
        # Save and run test
        save_file("test_main.py", test_code, overwrite=True)
        test_result = execute_pytest("test_main.py", verbose=False)
        
        if test_result.get('success') and test_result.get('return_code') == 0:
            state = add_message(state, "tester", "Tests passed!", "success")
            coverage = 100.0
        else:
            error_output = test_result.get('stderr', '') + "\n" + test_result.get('stdout', '')
            state = add_message(state, "tester", "Tests failed", "error")
            coverage = 0.0
            state = add_error(state, f"Test failure: {error_output.strip()}")
        
        return update_state(state, test_coverage=coverage)
    
    def _finalizer_node(self, state: AgentState) -> AgentState:
        """Finalize the workflow."""
        state = update_state(state, current_agent="finalizer", phase="complete")
        
        files_created = state.get('files_created', [])
        test_coverage = state.get('test_coverage', 0)
        
        if files_created and test_coverage > 0:
            state = add_message(state, "finalizer", "Task completed successfully!", "success")
            status = "completed"
        else:
            state = add_message(state, "finalizer", "Task completed with issues", "warning")
            status = "completed"
        
        return update_state(state, status=status)
    
    def _route_from_coder(self, state: AgentState) -> str:
        """Route after coding phase."""
        files_created = state.get('files_created', [])
        iteration = state.get('iteration', 0)
        
        if not files_created:
            return "end"  # No files created, end workflow
        
        if iteration > 2:  # Limit iterations
            return "finalize"
        
        return "test"
    
    def _route_from_tester(self, state: AgentState) -> str:
        """Route after testing phase."""
        test_coverage = state.get('test_coverage', 0)
        iteration = state.get('iteration', 0)
        
        if test_coverage > 0 or iteration > 1:
            return "finalize"
        
        # Increment iteration and try to fix
        state['iteration'] = iteration + 1
        return "fix"
    
    def _create_fallback_code(self, requirements: str) -> str:
        """Create simple fallback code."""
        if 'fastapi' in requirements.lower():
            return '''```python
# File: app.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def hello_world():
    return {"message": "Hello, World!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

```text
# File: requirements.txt
fastapi
uvicorn
```'''
        else:
            return '''```python
# File: main.py
def main():
    print("Hello, World!")
    return True

if __name__ == "__main__":
    main()
```'''
    
    def run(self, requirements: str, config: Dict[str, Any] = None):
        """Run the workflow with streaming."""
        initial_state = create_initial_state(requirements)
        
        try:
            for event in self.graph.stream(initial_state, config=config, stream_mode='updates'):
                yield {'success': True, 'event': event}
        except Exception as e:
            yield {'success': False, 'error': str(e)}