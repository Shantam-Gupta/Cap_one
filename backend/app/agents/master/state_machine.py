"""17-State Finite State Machine Engine with Strict Transition Validation."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set

# pyrefly: ignore [missing-import]
from app.schemas.enums import TaskState


class IllegalStateTransitionError(Exception):
    """Raised when an unauthorized or invalid state transition is attempted."""
    def __init__(self, current_state: TaskState, target_state: TaskState, reason: str = ""):
        self.current_state = current_state
        self.target_state = target_state
        self.reason = reason
        super().__init__(
            f"Illegal state transition attempted from '{current_state.value}' to '{target_state.value}'. "
            f"Reason: {reason or 'Not permitted by FSM transition graph.'}"
        )


@dataclass
class TransitionLog:
    """Audit record of a validated state transition."""
    from_state: TaskState
    to_state: TaskState
    attempt: int
    agent_responsible: str
    reason: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class TaskStateMachine:
    """
    Formally enforces the 17-State Finite State Machine.
    Controls valid workflow graph while Master Agent provides the decision intelligence.
    """

    # Terminal states where no further standard transitions can originate
    TERMINAL_STATES: Set[TaskState] = {
        TaskState.COMPLETED,
        TaskState.FAILED,
        TaskState.CANCELLED,
    }

    # Strict transition graph
    ALLOWED_TRANSITIONS: Dict[TaskState, Set[TaskState]] = {
        TaskState.RECEIVED: {
            TaskState.PLANNING,
            TaskState.CANCELLED,
        },
        TaskState.PLANNING: {
            TaskState.PLAN_READY,
            TaskState.FAILED,
            TaskState.CANCELLED,
        },
        TaskState.PLAN_READY: {
            TaskState.GENERATING,
            TaskState.COMPLETED,
            TaskState.CANCELLED,
        },
        TaskState.GENERATING: {
            TaskState.SECURITY_CHECK,
            TaskState.COMPLETED,
            TaskState.FAILED,
            TaskState.CANCELLED,
        },
        TaskState.SECURITY_CHECK: {
            TaskState.EXECUTING,
            TaskState.BLOCKED,
            TaskState.CANCELLED,
        },
        TaskState.EXECUTING: {
            TaskState.OBSERVING,
            TaskState.TIMEOUT,
            TaskState.CANCELLED,
        },
        # From OBSERVING, Master Agent makes the decision:
        TaskState.OBSERVING: {
            TaskState.VALIDATING,
            TaskState.ANALYZING_FAILURE,
            TaskState.BLOCKED,
            TaskState.CANCELLED,
        },
        # From ANALYZING_FAILURE, Master decides whether to repair, replan, or fail:
        TaskState.ANALYZING_FAILURE: {
            TaskState.REPAIRING,
            TaskState.REPLANNING,
            TaskState.FAILED,
            TaskState.CANCELLED,
        },
        TaskState.REPAIRING: {
            TaskState.RETRYING,
            TaskState.FAILED,
            TaskState.CANCELLED,
        },
        TaskState.RETRYING: {
            TaskState.SECURITY_CHECK,
            TaskState.CANCELLED,
        },
        # From VALIDATING, Task Validator checks semantic deliverables:
        TaskState.VALIDATING: {
            TaskState.COMPLETED,
            TaskState.ANALYZING_FAILURE,  # Handles False Success (Exit 0, Wrong Output)
            TaskState.CANCELLED,
        },
        TaskState.REPLANNING: {
            TaskState.PLANNING,
            TaskState.FAILED,
            TaskState.CANCELLED,
        },
        # TIMEOUT is handled as a first-class Master recovery decision:
        TaskState.TIMEOUT: {
            TaskState.REPAIRING,   # Algorithmic redesign / chunking
            TaskState.REPLANNING,  # Subtask revision
            TaskState.FAILED,      # Repeated timeout threshold exceeded
            TaskState.CANCELLED,
        },
        # BLOCKED is a hard security violation that terminates into FAILED:
        TaskState.BLOCKED: {
            TaskState.FAILED,
        },
        TaskState.COMPLETED: set(),
        TaskState.FAILED: set(),
        TaskState.CANCELLED: set(),
    }

    def __init__(self, initial_state: TaskState = TaskState.RECEIVED):
        self._current_state: TaskState = initial_state
        self._history: List[TransitionLog] = []

    @property
    def current_state(self) -> TaskState:
        return self._current_state

    @property
    def is_terminal(self) -> bool:
        return self._current_state in self.TERMINAL_STATES

    @property
    def history(self) -> List[TransitionLog]:
        return list(self._history)

    def can_transition_to(self, target_state: TaskState) -> bool:
        """Checks if a transition from the current state to target_state is permitted."""
        allowed = self.ALLOWED_TRANSITIONS.get(self._current_state, set())
        return target_state in allowed

    def transition(
        self,
        target_state: TaskState,
        attempt: int = 1,
        agent_responsible: str = "master_agent",
        reason: str = "",
    ) -> TransitionLog:
        """
        Executes a validated transition to target_state.
        Throws IllegalStateTransitionError if the transition is prohibited.
        """
        if not self.can_transition_to(target_state):
            raise IllegalStateTransitionError(
                current_state=self._current_state,
                target_state=target_state,
                reason=reason,
            )

        log_entry = TransitionLog(
            from_state=self._current_state,
            to_state=target_state,
            attempt=attempt,
            agent_responsible=agent_responsible,
            reason=reason,
        )
        self._history.append(log_entry)
        self._current_state = target_state
        return log_entry
