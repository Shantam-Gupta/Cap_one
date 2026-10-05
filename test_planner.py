import asyncio
import os
from app.agents.planner.agent import PlannerAgent

async def test_planner():
    print("\n--- Planner Agent Interactive Test ---")
    
    # Check if the API key is set
    if not os.environ.get("GEMINI_API_KEY") and not os.environ.get("OPENAI_API_KEY"):
        print("⚠️ WARNING: No API Key found in your environment.")
        print("If it fails, make sure you set it in your terminal first.\n")
        
    # Let the user input their own task
    user_task = input("Enter a task for the planner agent: ")
    
    if not user_task.strip():
        print("No task provided. Exiting.")
        return
        
    print(f"\nThinking... Sending your task to the real LLM...")
    agent = PlannerAgent()
    
    # No mock this time, we are using the real agent!
    try:
        plan = await agent.plan(
            task_prompt=user_task,
            available_files=[],
            constraints=["Ensure it is efficient and modular"]
        )
        print("\n=== Plan Generated Successfully! ===")
        print(f"Goal: {plan.goal}")
        
        if plan.requirements:
            print(f"Requirements: {', '.join(plan.requirements)}")
            
        print(f"\nSubtasks ({len(plan.subtasks)} total):")
        for subtask in plan.subtasks:
            deps = f"(Dependencies: {subtask.dependencies})" if subtask.dependencies else "(No dependencies)"
            print(f" [{subtask.id}] {subtask.name} {deps}")
            if subtask.description:
                print(f"     -> {subtask.description}")
            
        if plan.expected_outputs:
            print("\nExpected Outputs:")
            for out in plan.expected_outputs:
                print(f" - {out.name} (Type: {out.type})")
                
    except Exception as e:
        print(f"\n❌ Error occurred during planning: {e}")

if __name__ == "__main__":
    asyncio.run(test_planner())
