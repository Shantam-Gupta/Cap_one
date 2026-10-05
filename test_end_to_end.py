import asyncio
import os
from app.agents.planner.agent import PlannerAgent
from app.agents.validator.agent import TaskValidationAgent
from app.agents.master.context import TaskContext, ExecutionRecord

async def run_scenario():
    if not os.environ.get("GEMINI_API_KEY") and not os.environ.get("OPENAI_API_KEY"):
        print("WARNING: No API Key found. This requires a real LLM.")
        return

    print("==============================================")
    print(" STEP 1: PLANNER AGENT")
    print("==============================================")
    planner = PlannerAgent()
    task_prompt = "Plan a detailed trip to Ladakh with a budget of 150k INR."
    
    print(f"User Task: {task_prompt}")
    print("Thinking... generating granular subtasks and expected outputs...")
    plan = await planner.plan(task_prompt=task_prompt)

    print("\n[PLAN GENERATED]")
    print(f"Goal: {plan.goal}")
    print("\nExpected Outputs to be verified by Validator:")
    for out in plan.expected_outputs:
        print(f" - {out.name} (Required: {out.required})")

    # Setup the shared Context
    context = TaskContext(task_id="ladakh-test", prompt=task_prompt)
    context.plan = plan
    validator = TaskValidationAgent()

    print("\n==============================================")
    print(" STEP 2: VALIDATOR (SCENARIO A - FALSE SUCCESS)")
    print("==============================================")
    # Simulate the coding agent running successfully (exit 0) but failing to create the files
    exec_fail = ExecutionRecord(
        attempt=1,
        exit_code=0,
        stdout="I have planned the trip but I didn't save any documents.",
        stderr="",
        duration_ms=100.0,
        cpu_usage_pct=1.0,
        memory_usage_mb=50.0,
        artifacts=[]  # Empty! No files generated.
    )
    context.record_execution(exec_fail)
    
    res_fail = await validator.validate_task(context)
    print(f"Validator Passed? : {res_fail.passed}")
    print(f"Score             : {res_fail.score}")
    print(f"False Success?    : {res_fail.is_false_success}")
    print(f"Explanation       : {res_fail.explanation}")


    print("\n==============================================")
    print(" STEP 3: VALIDATOR (SCENARIO B - TRUE SUCCESS)")
    print("==============================================")
    # Simulate the coding agent creating exactly the files the planner asked for
    fake_artifacts = []
    for out in plan.expected_outputs:
        # Give them a fake size of 5000 bytes so they pass the minimum file size check
        fake_artifacts.append({"filename": getattr(out, "name", str(out)), "file_size_bytes": 5000})
        
    exec_success = ExecutionRecord(
        attempt=2,
        exit_code=0,
        stdout="Successfully saved all itineraries and budgets to the requested files.",
        stderr="",
        duration_ms=100.0,
        cpu_usage_pct=1.0,
        memory_usage_mb=50.0,
        artifacts=fake_artifacts
    )
    context.record_execution(exec_success)
    context.artifacts = fake_artifacts  # Add this line to update the context!
    
    res_success = await validator.validate_task(context)
    print(f"Validator Passed? : {res_success.passed}")
    print(f"Score             : {res_success.score}")
    print(f"False Success?    : {res_success.is_false_success}")
    print(f"Explanation       : {res_success.explanation}")

if __name__ == "__main__":
    asyncio.run(run_scenario())
