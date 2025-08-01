# Workflow definition for the autonomous coding graph
import os
import sys
import re # Import the regular expression module
from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import autogen


# Add the parent directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph.state import AgentState, create_initial_state, update_state, add_message, add_error, mark_phase_complete, should_continue_workflow, get_workflow_summary
from agents.planner import PlannerAgent
from agents.coder import CoderAgent
from agents.tester import TesterAgent
from agents.critic import CriticAgent
from tools.file_system_tool import save_file, read_file, list_files, create_directory
from tools.shell_tool import execute_command, execute_pytest, install_package, run_python_script
from tools.dependency_management_tool import add_dependency_to_requirements, parse_requirements_file, install_requirements
from tools.llm_tool import LLMTool
from utils import extract_code_from_markdown

# Load environment variables
# Removed load_dotenv() call

class AutonomousCodingWorkflow:
    """
    Autonomous Coding Workflow using LangGraph.
    This orchestrates the interaction between all agents in the coding team.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the workflow with agent configuration.
        
        Args:
            config (Dict[str, Any]): Configuration for LLM and agents
        """
        self.memory = MemorySaver()
        self.config = config or self._get_default_config()
        self.agents = self._initialize_agents()
        # --- FIX: ENABLE THE LLM TOOL ---
        # This now correctly initializes the LLMTool, enabling the AI.
        self.llm_tool = self._initialize_llm_tool()
        self.graph = self._build_graph()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for the workflow."""
        # This function is now configured for Ollama
        ollama_api_key = "ollama" 
        
        return {
            "config_list": [
                {
                    "model": "codellama",  # Or any other model you have downloaded with Ollama
                    "api_key": ollama_api_key,
                    "base_url": "http://localhost:11434/v1", # The Ollama OAI-compatible endpoint
                }
            ],
            "temperature": 0.1,
            "max_tokens": 4000
        }
    
    def _initialize_agents(self) -> Dict[str, Any]:
        """Initialize all agents with the configuration."""
        return {
            "planner": PlannerAgent(self.config),
            "coder": CoderAgent(self.config),
            "tester": TesterAgent(self.config),
            "critic": CriticAgent(self.config)
        }
    
    def _initialize_llm_tool(self) -> LLMTool:
        """Initialize the LLM tool."""
        # --- FIX: THIS NOW RETURNS A REAL LLMTool INSTANCE ---
        # This change will make the workflow use the actual AI model
        # instead of the mock agents.
        print("--- LLM Tool ENABLED. Using model from config. ---")
        # We get the model name from the first config in the list.
        config_list = self.config.get("config_list", [{}])
        model_config = config_list[0] if config_list else {}
        
        model_name = model_config.get("model", "codellama")
        base_url = model_config.get("base_url")
        
        return LLMTool(api_key="ollama", model=model_name, base_url=base_url)
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        
        # Create the state graph
        workflow = StateGraph(AgentState)
        
        # Add nodes for each agent
        workflow.add_node("planner", self._planner_node)
        workflow.add_node("coder", self._coder_node)
        workflow.add_node("tester", self._tester_node)
        workflow.add_node("critic", self._critic_node)
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "planner",
            self._route_after_planning,
            {
                "coding": "coder",
                "testing": "tester",
                "reviewing": "critic",
                "complete": END
            }
        )
        
        workflow.add_conditional_edges(
            "coder",
            self._route_after_coding,
            {
                "testing": "tester",
                "reviewing": "critic",
                "complete": END
            }
        )
        
        workflow.add_conditional_edges(
            "tester",
            self._route_after_testing,
            {
                "reviewing": "critic",
                "coding": "coder",  # Back to coding if tests fail
                "complete": END
            }
        )
        
        workflow.add_conditional_edges(
            "critic",
            self._route_after_review,
            {
                "coding": "coder",  # Back to coding if review suggests changes
                "complete": END
            }
        )
        
        # Set the entry point
        workflow.set_entry_point("planner")
        
        return workflow.compile(checkpointer=self.memory)
    
    def _planner_node(self, state: AgentState) -> AgentState:
        """Planner agent node - creates implementation plan."""
        try:
            state = update_state(state, current_agent="planner", phase="planning")
            state = add_message(state, "planner", "Starting planning phase...", "info")
            
            if self.llm_tool:
                planning_prompt = f"""
                Create a detailed implementation plan for the following requirements:
                {state['requirements']}
                Consider the following aspects:
                1. Technical architecture and design
                2. File structure and organization (name the main file `joke_cli.py`)
                3. Dependencies and libraries needed (e.g., `requests`)
                4. A simple testing strategy.
                Provide a comprehensive plan that the coder can follow directly.
                """
                
                llm_result = self.llm_tool.generate_completion(planning_prompt, max_tokens=3000)
                
                if llm_result["success"]:
                    plan = llm_result["text"]
                    state = add_message(state, "planner", "Planning completed using LLM", "success")
                else:
                    plan = self._create_mock_plan(state['requirements'])
                    state = add_message(state, "planner", f"LLM failed, using fallback plan: {llm_result.get('error')}", "warning")
            else:
                plan = self._create_mock_plan(state['requirements'])
                state = add_message(state, "planner", "Planning completed with mock agent", "info")
            
            state = update_state(state, plan=plan)
            state = add_message(state, "planner", "Planning phase completed successfully", "success")
            
            return state
            
        except Exception as e:
            error_msg = f"Planning phase failed: {str(e)}"
            return add_error(state, error_msg)
    
    def _coder_node(self, state: AgentState) -> AgentState:
        """Coder agent node - implements code based on plan."""
        try:
            state = update_state(state, current_agent="coder", phase="coding")
            state = add_message(state, "coder", "Starting coding phase...", "info")
            
            if self.llm_tool:
                history = "\n".join([f"[{m.get('agent', 'system')}] {m.get('message', '')}" for m in state.get('messages', [])[-5:]])

                coding_prompt = f"""
                Based on the following plan, requirements, and recent conversation history, please write or correct the code.

                **Requirements:**
                {state['requirements']}

                **Plan:**
                {state['plan']}

                **Recent History (This includes errors from previous attempts):**
                {history}

                Your task is to provide the complete, corrected Python code. 
                - Address any errors from the history (e.g., ImportError, IndentationError).
                - Name the file correctly as specified in the requirements (`joke_cli.py`).
                - If a new library like 'requests' is needed, generate a `requirements.txt` file.

                Provide your response as markdown code blocks. For example:
                ```python
                # File: joke_cli.py
                import requests
                # ... rest of the code
                ```text
                # File: requirements.txt
                requests
                ```
                """
                
                llm_result = self.llm_tool.generate_completion(coding_prompt, max_tokens=4000)
                
                if llm_result["success"]:
                    code = llm_result["text"]
                    state = add_message(state, "coder", "Code generated using LLM", "success")
                else:
                    code = self._create_mock_code(state['requirements'], state['plan'])
                    state = add_message(state, "coder", f"LLM failed, using fallback code: {llm_result.get('error')}", "warning")
            else:
                code = self._create_mock_code(state['requirements'], state['plan'])
                state = add_message(state, "coder", "Code generated with mock agent", "info")
            
            code_blocks = extract_code_from_markdown(code)
            files_created_this_turn = []

            def find_filename_in_code(code_content):
                match = re.search(r"#\s*File:\s*([\w\._-]+)", code_content)
                if match:
                    return match.group(1)
                return None

            for i, block in enumerate(code_blocks):
                code_content = block.get('code', '')
                filename = find_filename_in_code(code_content) or f"file_{i+1}.txt"

                save_result = save_file(filename, code_content, overwrite=True)
                if save_result['success']:
                    files_created_this_turn.append(filename)
                    state = add_message(state, "coder", f"Created/Updated file: {filename}", "info")
            
            state = update_state(
                state, 
                code=code,
                files_created=list(set(state['files_created'] + files_created_this_turn))
            )
            state = add_message(state, "coder", f"Coding phase completed. {len(files_created_this_turn)} files touched.", "success")
            
            return state
            
        except Exception as e:
            error_msg = f"Coding phase failed: {str(e)}"
            return add_error(state, error_msg)
    
    def _tester_node(self, state: AgentState) -> AgentState:
        """Tester agent node - creates and runs tests."""
        try:
            state = update_state(state, current_agent="tester", phase="testing")
            state = add_message(state, "tester", "Starting testing phase...", "info")
            
            if "requirements.txt" in state.get('files_created', []):
                state = add_message(state, "tester", "requirements.txt found, installing dependencies...", "info")
                install_result = install_requirements("requirements.txt")
                if install_result['success']:
                    state = add_message(state, "tester", "Dependencies installed successfully.", "success")
                else:
                    error_msg = f"Dependency installation failed: {install_result.get('stderr')}"
                    state = add_message(state, "tester", error_msg, "error")
                    return add_error(state, error_msg)

            if self.llm_tool and state.get('code'):
                test_prompt = f"""
                Generate comprehensive pytest tests for the following Python code. The code is in a file named `joke_cli.py`.
                
                ```python
                {state['code']}
                ```
                
                Create a test file named `test_joke_cli.py`.
                - Mock any external API calls to `https://official-joke-api.appspot.com/random_joke`.
                - Test that the main function runs without errors.
                - Test the output format.
                """
                
                llm_result = self.llm_tool.generate_completion(test_prompt, max_tokens=3000)
                
                if llm_result["success"]:
                    test_code = llm_result["text"]
                    state = add_message(state, "tester", "Tests generated using LLM", "success")
                else:
                    test_code = self._create_mock_tests(state['code'])
                    state = add_message(state, "tester", "Tests generated with fallback", "warning")
            else:
                test_code = self._create_mock_tests(state.get('code', ''))
                state = add_message(state, "tester", "Tests generated with mock agent", "info")
            
            test_filename = "test_joke_cli.py"
            code_blocks = extract_code_from_markdown(test_code)
            if code_blocks:
                # Save only the first python code block found
                save_file(test_filename, code_blocks[0]['code'], overwrite=True)
            else:
                # If no code block is found, save the raw text, which might still be valid
                save_file(test_filename, test_code, overwrite=True)
            
            test_result = execute_pytest(test_path=".")
            
            if test_result.get('success') and test_result.get('return_code') == 0:
                state = add_message(state, "tester", "All tests passed successfully!", "success")
                state = update_state(state, tests=test_code, test_coverage=100.0)
            else:
                error_output = test_result.get('stderr', '') + "\n" + test_result.get('stdout', '')
                state = add_message(state, "tester", f"Tests failed: {error_output.strip()}", "warning")
                state = update_state(state, tests=test_code, test_coverage=0.0)
            
            return state
            
        except Exception as e:
            error_msg = f"Testing phase failed: {str(e)}"
            return add_error(state, error_msg)
    
    def _critic_node(self, state: AgentState) -> AgentState:
        """Critic agent node - reviews code and provides feedback."""
        try:
            state = update_state(state, current_agent="critic", phase="reviewing")
            state = add_message(state, "critic", "Starting code review phase...", "info")
            
            if self.llm_tool and state.get('code'):
                review_prompt = f"""
                Review the following code, which passed its tests. Ensure it meets the requirements.
                Requirements: {state['requirements']}
                Code: {state['code']}
                Provide a final verdict: APPROVED or NEEDS_REVISION.
                """
                
                llm_result = self.llm_tool.generate_completion(review_prompt, max_tokens=3000)
                
                if llm_result["success"]:
                    review = llm_result["text"]
                    review_score = self._extract_review_score(review)
                    state = add_message(state, "critic", "Code review completed using LLM", "success")
                else:
                    review = self._create_mock_review(state['code'], state['requirements'])
                    review_score = 8.5
                    state = add_message(state, "critic", "Code review completed with fallback", "warning")
            else:
                review = self._create_mock_review(state.get('code', ''), state['requirements'])
                review_score = 8.5
                state = add_message(state, "critic", "Code review completed with mock agent", "info")
            
            state = update_state(state, review=review, review_score=review_score)
            state = add_message(state, "critic", "Code review completed successfully", "success")
            
            return state
            
        except Exception as e:
            error_msg = f"Review phase failed: {str(e)}"
            return add_error(state, error_msg)
    
    def _create_mock_plan(self, requirements: str) -> str:
        return f"Mock plan for: {requirements}"
    
    def _create_mock_code(self, requirements: str, plan: str) -> str:
        return "```python\n# Mock code\nprint('hello world')\n```"
    
    def _create_mock_tests(self, code: str) -> str:
        return "```python\n# Mock tests\nimport pytest\ndef test_mock():\n    assert True\n```"
    
    def _create_mock_review(self, code: str, requirements: str) -> str:
        return "Mock review: APPROVED"
    
    def _extract_review_score(self, review: str) -> float:
        if 'APPROVED' in review.upper():
            return 9.0
        return 5.0
    
    def _route_after_planning(self, state: AgentState) -> str:
        if state.get('plan'):
            return "coding"
        return "complete"
    
    def _route_after_coding(self, state: AgentState) -> str:
        if state.get('code'):
            return "testing"
        return "complete"
    
    def _route_after_testing(self, state: AgentState) -> str:
        if state.get('test_coverage', 0) > 80.0:
            state['iteration'] = 0  # Reset iteration count on success
            return "reviewing"
        
        # Increment iteration count and check against a limit
        iteration = state.get('iteration', 0) + 1
        state['iteration'] = iteration
        if iteration > 5:
            add_message(state, "system", "Exceeded max test-fix iterations.", "error")
            return "complete"
        return "coding"
    
    def _route_after_review(self, state: AgentState) -> str:
        if state.get('review_score', 0) > 8.0:
            return "complete"
        
        iteration = state.get('iteration', 0) + 1
        state['iteration'] = iteration
        if iteration > 7: # Allow a few more loops for review fixes
            add_message(state, "system", "Exceeded max review-fix iterations.", "error")
            return "complete"
        return "coding"
    
    def run(self, requirements: str, config: Dict[str, Any] = None):
        initial_state = create_initial_state(requirements)
        
        try:
            for event in self.graph.stream(initial_state, config=config, stream_mode='updates'):
                yield {'success': True, 'event': event}
        except Exception as e:
            yield {'success': False, 'error': str(e)}
    
    def get_workflow_status(self, config_id: str) -> Dict[str, Any]:
        try:
            state = self.memory.get(config_id)
            if state:
                summary = get_workflow_summary(state)
                return {"success": True, "state": state, "summary": summary}
            else:
                return {"success": False, "error": "Workflow not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}
