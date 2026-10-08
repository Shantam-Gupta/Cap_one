"""Master Agent Task Context and Execution Memory."""
import difflib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.schemas.enums import ErrorType, TaskState


@dataclass
class CodeVersion:
    """Represents an immutable code snapshot in execution history."""
    version: int  # 1 for attempt_1, 2 for attempt_2, etc.
    version_tag: str  # "attempt_1"
    source_code: str
    entrypoint: str
    dependencies: List[str]
    agent: str
    parent_version: Optional[int]
    modification_reason: str
    diff_from_parent: Optional[str]
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ExecutionRecord:
    """Runtime result of executing a code version in the sandbox."""
    attempt: int
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    cpu_usage_pct: float
    memory_usage_mb: float
    artifacts: List[Dict[str, Any]]
    oom_killed: bool = False
    timeout: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ErrorRecord:
    """Classified error from execution."""
    attempt: int
    error_type: ErrorType
    error_message: str
    traceback_clean: str
    failing_line: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class RepairRecord:
    """Diagnosis and proposed fix from Recovery Agent."""
    attempt: int
    diagnosis: str
    error_type: ErrorType
    repair_strategy: str
    confidence: float
    needs_replan: bool
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ValidationRecord:
    """Semantic task-level verification output."""
    attempt: int
    passed: bool
    score: float
    checks: List[Dict[str, Any]]
    failures: List[str]
    explanation: str
    is_false_success: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class TaskContext:
    """Master Agent's comprehensive state and execution memory across attempts."""
    task_id: str
    prompt: str
    max_retries: int = 3
    current_state: TaskState = TaskState.RECEIVED
    current_attempt: int = 1
    is_coding_task: bool = True
    files_available: List[str] = field(default_factory=list)
    plan: Optional[Dict[str, Any]] = None
    code_versions: List[CodeVersion] = field(default_factory=list)
    execution_history: List[ExecutionRecord] = field(default_factory=list)
    error_history: List[ErrorRecord] = field(default_factory=list)
    repair_history: List[RepairRecord] = field(default_factory=list)
    validation_history: List[ValidationRecord] = field(default_factory=list)
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    
    # Repeated failure tracking
    repeated_error_counts: Dict[str, int] = field(default_factory=dict)
    consecutive_identical_errors: int = 0
    last_error_signature: Optional[str] = None

    # Timing & limits
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    total_duration_sec: float = 0.0

    def add_code_version(
        self,
        source_code: str,
        entrypoint: str = "main.py",
        dependencies: Optional[List[str]] = None,
        agent: str = "coding_agent",
        modification_reason: str = "Initial generation",
    ) -> CodeVersion:
        """Registers a new immutable code version and computes unified diff with parent."""
        version_num = len(self.code_versions) + 1
        version_tag = f"attempt_{version_num}"
        parent_version = self.code_versions[-1].version if self.code_versions else None
        
        diff_text = None
        if self.code_versions:
            parent_code = self.code_versions[-1].source_code.splitlines(keepends=True)
            new_code = source_code.splitlines(keepends=True)
            diff = difflib.unified_diff(
                parent_code,
                new_code,
                fromfile=f"attempt_{parent_version}.py",
                tofile=f"{version_tag}.py",
                lineterm="",
            )
            diff_text = "".join(diff)

        cv = CodeVersion(
            version=version_num,
            version_tag=version_tag,
            source_code=source_code,
            entrypoint=entrypoint,
            dependencies=dependencies or [],
            agent=agent,
            parent_version=parent_version,
            modification_reason=modification_reason,
            diff_from_parent=diff_text,
        )
        self.code_versions.append(cv)
        return cv

    def record_execution(self, record: ExecutionRecord):
        """Appends execution metrics and outputs."""
        self.execution_history.append(record)

    def record_error(self, record: ErrorRecord):
        """Records an error and updates anti-looping repeated failure counters."""
        self.error_history.append(record)
        
        # Error signature combines type and first line of error message
        signature = f"{record.error_type}:{record.error_message.strip().splitlines()[0] if record.error_message else ''}"
        self.repeated_error_counts[signature] = self.repeated_error_counts.get(signature, 0) + 1
        
        if self.last_error_signature == signature:
            self.consecutive_identical_errors += 1
        else:
            self.consecutive_identical_errors = 1
            self.last_error_signature = signature

    def record_repair(self, record: RepairRecord):
        """Appends diagnosis and repair details."""
        self.repair_history.append(record)

    def record_validation(self, record: ValidationRecord):
        """Appends validation assessment."""
        self.validation_history.append(record)

    def is_repeated_failure(self, threshold: int = 2) -> bool:
        """Determines if the exact same failure has repeated consecutively."""
        return self.consecutive_identical_errors >= threshold

    def get_latest_code(self) -> Optional[CodeVersion]:
        """Returns the most recent code version."""
        return self.code_versions[-1] if self.code_versions else None

    def get_latest_execution(self) -> Optional[ExecutionRecord]:
        """Returns the most recent execution record."""
        return self.execution_history[-1] if self.execution_history else None

    def get_latest_error(self) -> Optional[ErrorRecord]:
        """Returns the most recent error record."""
        return self.error_history[-1] if self.error_history else None

    def get_latest_validation(self) -> Optional[ValidationRecord]:
        """Returns the most recent validation record."""
        return self.validation_history[-1] if self.validation_history else None

    def to_summary_dict(self) -> Dict[str, Any]:
        """Returns a comprehensive structured summary for API responses and traces."""
        return {
            "task_id": self.task_id,
            "prompt": self.prompt,
            "state": self.current_state.value,
            "current_attempt": self.current_attempt,
            "max_retries": self.max_retries,
            "total_attempts": len(self.code_versions),
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "plan": self.plan,
            "latest_code": self.get_latest_code().source_code if self.get_latest_code() else None,
            "latest_exit_code": self.get_latest_execution().exit_code if self.get_latest_execution() else None,
            "validation_passed": self.get_latest_validation().passed if self.get_latest_validation() else False,
            "artifacts_count": len(self.artifacts),
            "artifacts": self.artifacts,
            "repeated_failures_detected": self.is_repeated_failure(),
        }
