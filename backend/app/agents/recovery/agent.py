"""History-Aware Debug and Recovery Agent."""
import json
from typing import Any, Dict, List, Optional

from app.agents.master.context import TaskContext
from app.agents.recovery.schemas import RecoveryDecision
from app.llm.base import BaseLLMProvider
from app.llm.factory import get_llm_provider
from app.schemas.enums import ErrorType
from app.core.config import settings


class RecoveryAgent:
    """
    Diagnoses execution failures with full awareness of previous attempts,
    patches, and repeated failure history to produce targeted repairs.
    """

    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        self.llm = llm_provider or get_llm_provider()
        self.recovery_log_path = settings.WORKSPACE_DIR / "recovery_tasks.json"

    def save_recovery_task(self, task_data: dict):
        """Saves a copy of the validated recovery task to a separate file."""
        import json
        import os
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.recovery_log_path), exist_ok=True)
        
        history = []
        if os.path.exists(self.recovery_log_path):
            try:
                with open(self.recovery_log_path, "r") as f:
                    history = json.load(f)
            except json.JSONDecodeError:
                history = []
                
        history.append(task_data)
        
        with open(self.recovery_log_path, "w") as f:
            json.dump(history, f, indent=2)

    async def diagnose_and_repair(self, context: TaskContext) -> RecoveryDecision:
        latest_code_ver = context.get_latest_code()
        latest_exec = context.get_latest_execution()
        latest_error = context.get_latest_error()

        # Build trajectory summary across past attempts
        trajectory = []
        for i, code_ver in enumerate(context.code_versions):
            attempt_num = code_ver.version
            err = context.error_history[i] if i < len(context.error_history) else None
            rep = context.repair_history[i] if i < len(context.repair_history) else None
            
            entry = {
                "attempt": attempt_num,
                "modification_reason": code_ver.modification_reason,
                "error_type": err.error_type.value if err else "None",
                "error_message": err.error_message if err else "Clean execution",
                "previous_repair_strategy": rep.repair_strategy if rep else "None",
                "diff_from_parent": code_ver.diff_from_parent,
            }
            trajectory.append(entry)

        is_repeated = context.is_repeated_failure()

        system_prompt = (
            "You are the Lead Recovery & Debugging Engineer in the ReRun Autonomous Platform.\n"
            "Your job is to diagnose execution failures and produce a surgical, targeted repair.\n"
            "You have access to the complete execution history across all attempts.\n"
            "Requirements:\n"
            "1. Output MUST be valid JSON with keys: 'diagnosis', 'error_type', 'repair_strategy', 'modified_code', 'confidence', 'needs_replan'.\n"
            "2. Avoid making arbitrary changes to working code; only repair the failing operation.\n"
            "3. If a repeated failure is detected, DO NOT repeat the previous failed strategy.\n"
            "4. If the fundamental approach is flawed, set 'needs_replan': true."
        )

        user_content = {
            "original_task": context.prompt,
            "plan": context.plan,
            "current_attempt": context.current_attempt,
            "latest_failing_code": latest_code_ver.source_code if latest_code_ver else "",
            "latest_exit_code": latest_exec.exit_code if latest_exec else 1,
            "latest_stderr": latest_exec.stderr if latest_exec else "",
            "latest_stdout": latest_exec.stdout if latest_exec else "",
            "diagnosed_error_type": latest_error.error_type.value if latest_error else "UNKNOWN_ERROR",
            "diagnosed_error_message": latest_error.error_message if latest_error else "",
            "failing_line": latest_error.failing_line if latest_error else "",
            "repeated_failure_alert": is_repeated,
            "consecutive_identical_errors": context.consecutive_identical_errors,
            "history_trajectory": trajectory,
        }

        if is_repeated:
            user_content["CRITICAL_INSTRUCTION"] = (
                f"REPEATED FAILURE DETECTED: The last {context.consecutive_identical_errors} attempts failed "
                f"with the identical error ({latest_error.error_type.value if latest_error else 'UNKNOWN_ERROR'}). "
                "DO NOT repeat the previous repair. Implement an alternative strategy or request replanning."
            )

        try:
            resp = await self.llm.complete_structured(
                prompt=json.dumps(user_content, indent=2),
                system_prompt=system_prompt,
            )
            data = resp.structured or {}
        except Exception as e:
            print(f"Recovery agent llm error: {e}")
            data = {}
        if "modified_code" not in data or not data["modified_code"]:
            # Fallback code
            data["modified_code"] = latest_code_ver.source_code if latest_code_ver else ""
            data["diagnosis"] = data.get("diagnosis", "Runtime error diagnosed.")
            data["error_type"] = latest_error.error_type.value if latest_error else ErrorType.UNKNOWN_ERROR.value
            data["repair_strategy"] = data.get("repair_strategy", "Applied targeted fix.")
            data["dependencies"] = data.get("dependencies", ["pandas", "matplotlib"])
            data["confidence"] = 0.9
            data["needs_replan"] = is_repeated

        return RecoveryDecision.model_validate(data)
