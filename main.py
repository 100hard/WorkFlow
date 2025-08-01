import os
import sys
import uuid
from dotenv import load_dotenv

# Ensure local imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph.workflow import AutonomousCodingWorkflow
from graph.state import get_workflow_summary

def main():
    print("\n🚀 Autonomous Coding Team - Main Application")
    print("============================================\n")

    # Load environment variables
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    # NOTE: For Ollama, the API key isn't used but the check remains.
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment. Please set it in your .env file.")
        return

    # Force the use of the local Ollama server by setting the base URL environment variable
    os.environ["OPENAI_API_BASE"] = "http://localhost:11434/v1"

    # Get requirements from user
    print("Please enter your high-level project requirements (or type 'exit' to quit):")
    requirements = input("> ").strip()
    if requirements.lower() == "exit":
        print("👋 Exiting application.")
        return

    # Initialize workflow
    try:
        workflow = AutonomousCodingWorkflow()
    except Exception as e:
        print(f"❌ Failed to initialize workflow: {e}")
        return

    print("\n🧠 Running Autonomous Coding Workflow...\n")
    try:
        thread_id = str(uuid.uuid4())
        
        # --- FIX 1: INCREASE RECURSION LIMIT ---
        # We increase the limit to give the agent more attempts to fix the code,
        # which is especially useful with local models.
        config = {
            "recursion_limit": 50,
            "configurable": {
                "thread_id": thread_id
            }
        }
        
        last_printed_message_index = -1
        final_state = {}
        
        # Pass the updated config to the workflow run
        for result in workflow.run(requirements, config=config):
            if not result.get('success'):
                print(f"❌ Workflow failed: {result.get('error')}")
                return

            event = result.get('event')
            if isinstance(event, dict):
                for agent, state in event.items():
                    final_state = state  # Always update to the latest state
                    messages = state.get('messages')
                    if isinstance(messages, list):
                        new_messages_count = len(messages) - (last_printed_message_index + 1)
                        if new_messages_count > 0:
                            print(f"\n--- 🧑‍💻 Agent: {agent.capitalize()} ---")
                            new_messages = messages[last_printed_message_index + 1:]
                            for msg in new_messages:
                                # --- FIX 2: IMPROVE MESSAGE LOGGING ---
                                # This will now correctly print the detailed error messages,
                                # so you can see the actual `ImportError` from pytest.
                                if isinstance(msg, dict) and 'message' in msg:
                                    msg_type = msg.get('type', 'info').upper()
                                    print(f"    [{msg_type}] {msg['message']}")
                                else:
                                    # Fallback for any unexpected message format
                                    print(f"    {msg}")
                            last_printed_message_index = len(messages) - 1

        # Final summary
        summary = get_workflow_summary(final_state)
        print("\n✅ Workflow completed successfully!")
        print("============================================")
        print("Workflow Summary:")
        for k, v in summary.items():
            print(f"- {k}: {v}")
        print("\n📋 For detailed results, check the generated files and logs.")

    except Exception as e:
        print(f"❌ Workflow execution failed: {e}")
        return

if __name__ == "__main__":
    main()
