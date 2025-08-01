import sys
import os
import pytest
from unittest.mock import patch
from dotenv import load_dotenv

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from graph.workflow import AutonomousCodingWorkflow

# Load environment variables for tests
load_dotenv()

@patch('uuid.uuid4', return_value='test-uuid')
def test_workflow_runs_without_errors(mock_uuid):
    """Test that the workflow runs to completion without raising exceptions."""
    workflow = AutonomousCodingWorkflow()
    requirements = "Create a simple FastAPI application."
    
    try:
        for _ in workflow.run(requirements, configurable={"thread_id": "test-uuid"}):
            pass
    except Exception as e:
        pytest.fail(f"Workflow raised an unexpected exception: {e}")
