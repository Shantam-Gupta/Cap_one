import asyncio
from app.agents.validator.agent import TaskValidationAgent
from app.agents.master.context import TaskContext, ExecutionRecord
from app.agents.planner.schemas import PlanOutput, ExpectedOutput

async def test_validator():
    print("Testing TaskValidationAgent...")
    agent = TaskValidationAgent()
    
    # Set up a mock TaskContext
    context = TaskContext(
        task_id="test-1",
        prompt="Create a sales chart",
        artifacts=[{"filename": "sales_chart.png", "file_size_bytes": 1024}]
    )
    
    # Add a fake execution record (Exit code 0 = script ran without crashing)
    exec_record = ExecutionRecord(
        attempt=1,
        exit_code=0,
        stdout="Calculated total revenue: $5000",
        stderr="",
        duration_ms=100.0,
        cpu_usage_pct=5.0,
        memory_usage_mb=50.0,
        artifacts=[{"filename": "sales_chart.png", "file_size_bytes": 1024}]
    )
    context.record_execution(exec_record)

    # --- Test Scenario 1: plan is a Pydantic Object ---
    print("\n[Test 1] Testing with Pydantic PlanOutput Object (This used to crash):")
    context.plan = PlanOutput(
        goal="Make a chart",
        expected_outputs=[ExpectedOutput(name="sales_chart.png", type="image", required=True)]
    )
    
    try:
        res1 = await agent.validate_task(context)
        print(f" -> SUCCESS! No crash.")
        print(f" -> Validator result: Passed={res1.passed}, Score={res1.score}")
        print(f" -> Explanation: {res1.explanation}")
    except Exception as e:
        print(f" -> CRASH in Test 1: {e}")

    # --- Test Scenario 2: plan is a Dictionary ---
    print("\n[Test 2] Testing with a basic Python Dictionary:")
    context.plan = {
        "expected_outputs": [{"name": "sales_chart.png", "type": "image", "required": True}]
    }
    
    try:
        res2 = await agent.validate_task(context)
        print(f" -> SUCCESS! No crash.")
        print(f" -> Validator result: Passed={res2.passed}, Score={res2.score}")
    except Exception as e:
        print(f" -> CRASH in Test 2: {e}")

if __name__ == "__main__":
    asyncio.run(test_validator())
