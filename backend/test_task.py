import asyncio
import sys
import uuid
from app.agents.master.orchestrator import MasterAgentOrchestrator

async def run_demo(prompt: str):
    task_id = f"demo_task_{uuid.uuid4().hex[:8]}"
    print(f"\n--- Initializing ReRun Orchestrator for Task: {task_id} ---")
    print(f"Prompt: {prompt}\n")

    # Initialize Master Orchestrator
    orchestrator = MasterAgentOrchestrator(
        task_id=task_id,
        prompt=prompt
    )

    # Run the autonomous flow
    summary = await orchestrator.run()

    print("\n--- Task Execution Complete ---")
    print("Final Summary:")
    
    import json
    for key, value in summary.items():
        if key == "plan" and value:
            print("\n  [OUTPUT PLAN]:")
            print(json.dumps(value, indent=2))
            print()
        elif key == "artifacts" and value:
            print(f"  [ARTIFACTS]: {len(value)} files generated.")
        else:
            print(f"  {key}: {value}")
    
    print("\nCheck the recovery_tasks.json in the workspace directory to verify the recovery agent saved a copy!")

if __name__ == "__main__":
    import os
    
    # Check for API key
    if not os.environ.get("GEMINI_API_KEY"):
        print("GEMINI_API_KEY is not set in your environment.")
        api_key = input("Please enter your Gemini API Key: ").strip()
        if api_key:
            os.environ["GEMINI_API_KEY"] = api_key
        else:
            print("Warning: Running without an API key might cause failures.")
            
    print("\n==========================================")
    print("      ReRun Agent Testing Interface")
    print("==========================================")
    
    user_prompt = input("\nPlease enter the task you want the agent to perform:\n> ").strip()
    
    if not user_prompt:
        print("No task provided. Exiting...")
        sys.exit(0)
        
    asyncio.run(run_demo(user_prompt))
