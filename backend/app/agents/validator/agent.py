"""Task Validation Agent and False-Success Detector."""
from typing import Any, Dict, List, Optional

from app.agents.master.context import TaskContext
from app.agents.validator.rules import SemanticValidationRules
from app.agents.validator.schemas import TaskValidationResult, ValidationCheck
from app.llm.base import BaseLLMProvider
from app.llm.factory import get_llm_provider

class TaskValidationAgent:
    """
    Evaluates whether the user's substantive task requirements were truly satisfied.
    Crucially separates Execution Success (exit code 0) from Task Success.
    """

    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        self.llm = llm_provider or get_llm_provider()

    async def validate_task(self, context: TaskContext) -> TaskValidationResult:
        latest_exec = context.get_latest_execution()
        plan = context.plan or {}

        # 1. Deterministic Deliverable Check
        if hasattr(plan, "expected_outputs"):
            expected_outputs = plan.expected_outputs
        elif isinstance(plan, dict):
            expected_outputs = plan.get("expected_outputs", [])
        else:
            expected_outputs = []
            
        if not expected_outputs:
            # Infer standard deliverables from prompt
            prompt_l = context.prompt.lower()
            if "chart" in prompt_l or "plot" in prompt_l or "visualiz" in prompt_l:
                expected_outputs = [{"name": "sales_chart.png", "type": "image", "required": True}]

        checks, failures = SemanticValidationRules.check_file_deliverables(
            expected_outputs=expected_outputs,
            actual_artifacts=context.artifacts,
        )

        # 2. Check stdout calculations
        stdout = latest_exec.stdout if latest_exec else ""
        calc_checks, calc_failures = SemanticValidationRules.check_stdout_calculations(
            stdout=stdout,
            task_prompt=context.prompt,
        )
        checks.extend(calc_checks)
        failures.extend(calc_failures)

        # False success detection: Program exited 0, but deliverables failed
        is_false_success = False
        if latest_exec and latest_exec.exit_code == 0 and failures:
            is_false_success = True

        passed = (len(failures) == 0)
        score = 1.0 if passed else max(0.0, 1.0 - (len(failures) * 0.4))

        if passed:
            explanation = "All requested deliverables, charts, and calculations were verified successfully."
        elif is_false_success:
            explanation = (
                f"FALSE SUCCESS DETECTED: Execution completed cleanly with exit code 0, "
                f"but semantic deliverables failed validation: {'; '.join(failures)}"
            )
        else:
            explanation = f"Task validation failed: {'; '.join(failures)}"

        parsed_checks = [ValidationCheck(**c) for c in checks]

        return TaskValidationResult(
            passed=passed,
            score=round(score, 2),
            checks=parsed_checks,
            failures=failures,
            explanation=explanation,
            is_false_success=is_false_success,
        )
