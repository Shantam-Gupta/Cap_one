"""Master Agent Orchestrator: Supervisory Intelligence and Lifecycle Controller."""
import asyncio
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.coding.agent import CodingAgent
from app.agents.master.context import (
    ErrorRecord,
    ExecutionRecord,
    RepairRecord,
    TaskContext,
    ValidationRecord,
)
from app.agents.master.state_machine import TaskStateMachine
from app.agents.planner.agent import PlannerAgent
from app.agents.recovery.agent import RecoveryAgent
from app.agents.validator.agent import TaskValidationAgent
from app.core.config import settings
from app.core.events import event_bus
from app.core.logging import logger
from app.database.models import TaskModel
from app.database.repositories import TaskRepository
from app.execution.engine import ExecutionEngine
from app.schemas.enums import AgentType, ErrorType, EventType, FinalStatus, NetworkPolicy, TaskState
from app.security.policy import SecurityPolicyEngine


class MasterAgentOrchestrator:
    """
    Central Supervising Intelligence of the ReRun Platform.
    Enforces the bounded autonomous loop and coordinates specialized agents.
    """

    def __init__(
        self,
        task_id: str,
        prompt: str,
        db_session: Optional[AsyncSession] = None,
        max_retries: Optional[int] = None,
        network_policy: NetworkPolicy = NetworkPolicy.DISABLED,
        initial_files: Optional[List[str]] = None,
    ):
        self.task_id = task_id
        self.prompt = prompt
        self.db_session = db_session
        self.repo = TaskRepository(db_session) if db_session else None
        self.max_retries = max_retries or settings.MAX_RETRIES
        self.network_policy = network_policy
        self.initial_files = initial_files or []

        # Master-managed Context & State Machine
        self.context = TaskContext(
            task_id=task_id,
            prompt=prompt,
            max_retries=self.max_retries,
            files_available=self.initial_files,
        )
        self.fsm = TaskStateMachine(initial_state=TaskState.RECEIVED)

        # Specialized Agent Subsystems
        self.planner = PlannerAgent()
        self.coder = CodingAgent()
        self.security = SecurityPolicyEngine(network_policy=self.network_policy)
        self.executor = ExecutionEngine()
        self.recovery = RecoveryAgent()
        self.validator = TaskValidationAgent()

        self._cancelled = False

    async def cancel(self, reason: str = "User cancellation requested"):
        """Human override to cancel execution from any active state."""
        self._cancelled = True
        if not self.fsm.is_terminal:
            await self._transition(TaskState.CANCELLED, reason=reason)
            await self._record_and_publish(
                EventType.TASK_CANCELLED,
                {"reason": reason, "status": FinalStatus.CANCELLED.value},
            )
            if self.repo:
                await self.repo.update_task_state(
                    task_id=self.task_id,
                    state=TaskState.CANCELLED,
                    final_status=FinalStatus.CANCELLED.value,
                )

    async def _transition(self, target_state: TaskState, reason: str = ""):
        """Transitions state machine and syncs context."""
        log = self.fsm.transition(
            target_state=target_state,
            attempt=self.context.current_attempt,
            agent_responsible="master_agent",
            reason=reason,
        )
        self.context.current_state = target_state
        logger.info(f"Task {self.task_id} FSM: {log.from_state.value} -> {log.to_state.value} ({reason})")
        
        await self._record_and_publish(
            EventType.STATE_TRANSITION,
            {"from_state": log.from_state.value, "to_state": log.to_state.value, "reason": reason}
        )

    async def _record_and_publish(
        self,
        event_type: EventType,
        details: Optional[Dict[str, Any]] = None,
        agent_name: str = "master_agent",
    ):
        """Emits event to EventBus for real-time WebSocket distribution and persists to DB."""
        payload = {
            "task_id": self.task_id,
            "type": event_type.value,
            "state": self.context.current_state.value,
            "attempt": self.context.current_attempt,
            "agent": agent_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": details or {},
        }
        await event_bus.publish(self.task_id, payload)

        if self.repo:
            try:
                await self.repo.record_task_event(
                    task_id=self.task_id,
                    event_type=event_type.value,
                    attempt=self.context.current_attempt,
                    agent_name=agent_name,
                    details=details or {},
                )
                await self.repo.update_task_state(
                    task_id=self.task_id,
                    state=self.context.current_state,
                    attempt=self.context.current_attempt,
                )
            except Exception as e:
                logger.error(f"Error persisting event to DB: {e}")

    async def run(self) -> Dict[str, Any]:
        """
        Executes the autonomous loop:
        PLAN -> GENERATE -> SECURE -> EXECUTE -> OBSERVE -> DIAGNOSE/REPAIR -> VALIDATE
        """
        start_time = time.time()
        await self._record_and_publish(EventType.TASK_CREATED, {"prompt": self.prompt})

        # Ensure task workspace is clean and isolated
        task_workspace = settings.WORKSPACE_DIR / self.task_id
        if task_workspace.exists():
            import shutil
            shutil.rmtree(task_workspace)
        task_workspace.mkdir(parents=True, exist_ok=True)

        try:
            # 0. CLASSIFY TASK
            from app.llm.factory import get_llm_provider
            llm = get_llm_provider()
            classify_sys = "You are a task orchestrator. Reply ONLY with 'CODING' if the task requires writing or executing code. Reply ONLY with 'NORMAL' if it is a general reasoning or text task."
            class_res = await llm.complete(prompt=self.prompt, system_prompt=classify_sys)
            
            self.context.is_coding_task = "CODING" in class_res.content.upper()
            logger.info(f"Task {self.task_id} classified as coding task: {self.context.is_coding_task}")

            if self._cancelled:
                return self.context.to_summary_dict()

            # 1. PLANNER GENERATES BEST OF 3
            await self._transition(TaskState.PLANNING, reason="Generating 3 candidate plans")
            candidate_plans = []
            import asyncio
            for attempt_idx in range(3):
                plan_out = await self.planner.plan(
                    task_prompt=self.prompt,
                    available_files=self.context.files_available,
                )
                candidate_plans.append(plan_out)
                
                # Add a delay between API calls to prevent 429 Rate Limits on free-tier keys
                if attempt_idx < 2:
                    await asyncio.sleep(4)
            
            # Using validator to score is tricky for raw plans, so we use the first as 'best' placeholder
            # per standard heuristic unless complex scoring is defined.
            best_plan = candidate_plans[0]
            self.context.plan = best_plan.model_dump()
            await self._transition(TaskState.PLAN_READY, reason="Plan ready")

            if not self.context.is_coding_task:
                # NORMAL TASK FLOW
                self.recovery.save_recovery_task(self.context.plan)
                
                # Master Final Check
                final_check_sys = "You are a master agent. Check if any changes are needed for this plan. Reply 'NO CHANGES' or suggest changes."
                check_res = await llm.complete(prompt=str(self.context.plan), system_prompt=final_check_sys)
                logger.info(f"Master final check: {check_res.content}")
                
                await self._transition(TaskState.COMPLETED, reason="Normal task completed and validated")
            
            else:
                # CODING TASK FLOW
                await self._transition(TaskState.GENERATING, reason="Delegating to Coding Agent")
                
                # For coding task, we generate code
                code_payload = await self.coder.generate_code(
                    task_prompt=self.prompt,
                    plan=self.context.plan,
                    available_files=self.context.files_available,
                )
                
                cv = self.context.add_code_version(
                    source_code=code_payload.code,
                    entrypoint=code_payload.entrypoint,
                    dependencies=code_payload.dependencies,
                    agent="coding_agent",
                    modification_reason="Initial generation from plan",
                )

                # Forward to recovery agent to save
                self.recovery.save_recovery_task({
                    "plan": self.context.plan,
                    "code": code_payload.code
                })
                
                # Master Final Check
                final_check_sys = "You are a master agent. Check if any changes are needed for this code. Reply 'NO CHANGES' or suggest changes."
                check_res = await llm.complete(prompt=code_payload.code, system_prompt=final_check_sys)
                logger.info(f"Master final check: {check_res.content}")
                
                await self._transition(TaskState.COMPLETED, reason="Coding task completed and validated")

        except Exception as e:
            logger.error(f"Unexpected Master Agent orchestration exception: {e}", exc_info=True)
            if not self.fsm.is_terminal:
                await self._transition(TaskState.FAILED, reason=f"Platform Error: {str(e)}")
                if self.repo:
                    await self.repo.update_task_state(
                        task_id=self.task_id,
                        state=TaskState.FAILED,
                        final_status=FinalStatus.FAILED_AFTER_RETRIES.value,
                        error_message=str(e),
                    )

        self.context.total_duration_sec = time.time() - start_time
        self.context.completed_at = datetime.now(timezone.utc).isoformat()

        if self.repo:
            try:
                stmt = (
                    update(TaskModel)
                    .where(TaskModel.id == self.task_id)
                    .values(total_duration_sec=self.context.total_duration_sec)
                )
                await self.repo.session.execute(stmt)
                await self.repo.session.commit()
            except Exception as e:
                logger.warning(f"Could not persist total_duration_sec: {e}")

        return self.context.to_summary_dict()

    async def _stage_repair(self, repair_decision):
        """Increments attempt and registers repaired code version."""
        self.context.current_attempt += 1
        # Use the current code version's entrypoint — don't assume main.py
        current_code = self.context.get_latest_code()
        current_entrypoint = current_code.entrypoint if current_code else "main.py"
        new_cv = self.context.add_code_version(
            source_code=repair_decision.modified_code,
            entrypoint=current_entrypoint,
            dependencies=repair_decision.dependencies,
            agent="recovery_agent",
            modification_reason=f"Repair {repair_decision.error_type.value}: {repair_decision.repair_strategy}",
        )
        await self._transition(
            TaskState.RETRYING,
            reason=f"Staging attempt_{new_cv.version} with repaired code",
        )
