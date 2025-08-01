# State management for the autonomous coding workflow
from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime

class AgentState(TypedDict):
    """
    State management for the autonomous coding workflow.
    This defines the shared state that flows between agents in the graph.
    """
    
    # Core workflow data
    requirements: str
    plan: Optional[str]
    code: Optional[str]
    tests: Optional[str]
    review: Optional[str]
    
    # Agent communication
    messages: List[Dict[str, Any]]
    current_agent: Optional[str]
    
    # Workflow control
    phase: str  # "planning", "coding", "testing", "reviewing", "complete"
    iteration: int
    
    # Metadata
    start_time: datetime
    last_update: datetime
    status: str  # "in_progress", "completed", "failed", "needs_revision"
    
    # Error handling
    errors: List[str]
    warnings: List[str]
    
    # File management
    files_created: List[str]
    files_modified: List[str]
    
    # Quality metrics
    test_coverage: Optional[float]
    code_quality_score: Optional[float]
    review_score: Optional[float]

def create_initial_state(requirements: str) -> AgentState:
    """
    Create the initial state for a new coding workflow.
    
    Args:
        requirements (str): The initial requirements for the project
        
    Returns:
        AgentState: The initial state
    """
    now = datetime.now()
    
    return AgentState(
        requirements=requirements,
        plan=None,
        code=None,
        tests=None,
        review=None,
        messages=[],
        current_agent=None,
        phase="planning",
        iteration=1,
        start_time=now,
        last_update=now,
        status="in_progress",
        errors=[],
        warnings=[],
        files_created=[],
        files_modified=[],
        test_coverage=None,
        code_quality_score=None,
        review_score=None
    )

def update_state(state: AgentState, **updates) -> AgentState:
    """
    Update the state with new information.
    
    Args:
        state (AgentState): The current state
        **updates: Key-value pairs to update
        
    Returns:
        AgentState: The updated state
    """
    updated_state = state.copy()
    updated_state.update(updates)
    updated_state["last_update"] = datetime.now()
    return updated_state

def add_message(state: AgentState, agent_name: str, message: str, message_type: str = "info") -> AgentState:
    """
    Add a message to the state's message history.
    
    Args:
        state (AgentState): The current state
        agent_name (str): Name of the agent sending the message
        message (str): The message content
        message_type (str): Type of message ("info", "warning", "error", "success")
        
    Returns:
        AgentState: The updated state
    """
    new_message = {
        "agent": agent_name,
        "message": message,
        "type": message_type,
        "timestamp": datetime.now().isoformat()
    }
    
    updated_messages = state["messages"].copy()
    updated_messages.append(new_message)
    
    return update_state(state, messages=updated_messages)

def add_error(state: AgentState, error: str) -> AgentState:
    """
    Add an error to the state.
    
    Args:
        state (AgentState): The current state
        error (str): The error message
        
    Returns:
        AgentState: The updated state
    """
    updated_errors = state["errors"].copy()
    updated_errors.append(error)
    return update_state(state, errors=updated_errors)

def add_warning(state: AgentState, warning: str) -> AgentState:
    """
    Add a warning to the state.
    
    Args:
        state (AgentState): The current state
        warning (str): The warning message
        
    Returns:
        AgentState: The updated state
    """
    updated_warnings = state["warnings"].copy()
    updated_warnings.append(warning)
    return update_state(state, warnings=updated_warnings)

def mark_phase_complete(state: AgentState, phase: str) -> AgentState:
    """
    Mark a phase as complete and move to the next phase.
    
    Args:
        state (AgentState): The current state
        phase (str): The phase that was completed
        
    Returns:
        AgentState: The updated state
    """
    phase_order = ["planning", "coding", "testing", "reviewing"]
    
    try:
        current_index = phase_order.index(state["phase"])
        if current_index < len(phase_order) - 1:
            next_phase = phase_order[current_index + 1]
        else:
            next_phase = "complete"
    except ValueError:
        next_phase = "complete"
    
    return update_state(
        state,
        phase=next_phase,
        status="in_progress" if next_phase != "complete" else "completed"
    )

def should_continue_workflow(state: AgentState) -> bool:
    """
    Determine if the workflow should continue based on current state.
    
    Args:
        state (AgentState): The current state
        
    Returns:
        bool: True if workflow should continue, False otherwise
    """
    # Stop if we have too many errors
    if len(state["errors"]) > 5:
        return False
    
    # Stop if we've completed all phases
    if state["phase"] == "complete":
        return False
    
    # Stop if we've had too many iterations
    if state["iteration"] > 10:
        return False
    
    return True

def get_workflow_summary(state: AgentState) -> Dict[str, Any]:
    """
    Get a summary of the current workflow state.
    
    Args:
        state (AgentState): The current state
        
    Returns:
        Dict[str, Any]: Summary of the workflow
    """
    start_time = state.get("start_time")
    last_update = state.get("last_update")
    duration = (last_update - start_time).total_seconds() if start_time and last_update else 0

    return {
        "phase": state.get("phase", "Unknown"),
        "iteration": state.get("iteration", 0),
        "status": state.get("status", "Unknown"),
        "errors_count": len(state.get("errors", [])),
        "warnings_count": len(state.get("warnings", [])),
        "files_created": len(state.get("files_created", [])),
        "files_modified": len(state.get("files_modified", [])),
        "test_coverage": state.get("test_coverage"),
        "code_quality_score": state.get("code_quality_score"),
        "review_score": state.get("review_score"),
        "duration": duration
    }