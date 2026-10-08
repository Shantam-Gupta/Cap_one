"""Deterministic 15-Class Error Taxonomy Classifier."""
import re
from typing import Optional, Tuple

# pyrefly: ignore [missing-import]
from app.schemas.enums import ErrorType


class ErrorClassifier:
    """
    Deterministic rule-based error classifier analyzing tracebacks, exit codes, and output streams.
    """

    PATTERNS = [
        (ErrorType.TIMEOUT, [r"SandboxTimeout", r"TimeoutExpired", r"timed? out", r"ExecutionTimeoutExpired"]),
        (ErrorType.MEMORY_LIMIT, [r"MemoryError", r"OOMKilled", r"out of memory", r"killed process.*oom"]),
        (ErrorType.CPU_LIMIT, [r"CPU time limit exceeded"]),
        (ErrorType.SYNTAX_ERROR, [r"SyntaxError", r"IndentationError", r"TabError"]),
        (ErrorType.IMPORT_ERROR, [r"ModuleNotFoundError", r"ImportError"]),
        (ErrorType.KEY_ERROR, [r"KeyError"]),
        (ErrorType.INDEX_ERROR, [r"IndexError"]),
        (ErrorType.NAME_ERROR, [r"NameError", r"UnboundLocalError"]),
        (ErrorType.TYPE_ERROR, [r"TypeError"]),
        (ErrorType.VALUE_ERROR, [r"ValueError"]),
        (ErrorType.FILE_ERROR, [r"FileNotFoundError", r"PermissionError", r"IsADirectoryError", r"FileExistsError", r"No such file or directory"]),
        (ErrorType.NETWORK_ERROR, [r"ConnectionError", r"ConnectionRefusedError", r"NewConnectionError", r"Network is unreachable", r"socket\.gaierror"]),
        (ErrorType.SECURITY_VIOLATION, [r"SecurityViolation", r"Forbidden module", r"Prohibited function", r"path traversal"]),
        (ErrorType.OUTPUT_ERROR, [r"OutputValidationError", r"MissingArtifactError", r"Semantic Task Failure"]),
    ]

    @classmethod
    def classify(
        cls,
        exit_code: int,
        stderr: str,
        stdout: str = "",
        oom_killed: bool = False,
        timeout: bool = False,
    ) -> Tuple[ErrorType, str, Optional[str]]:
        """
        Returns (ErrorType, clean_error_message, failing_line).
        """
        combined = f"{stderr}\n{stdout}"

        if oom_killed or exit_code == 137:
            return ErrorType.MEMORY_LIMIT, "Process terminated: Sandbox memory limit exceeded (OOM killed).", None

        if timeout or exit_code == 124:
            return ErrorType.TIMEOUT, "Execution timed out: Sandbox execution duration limit exceeded.", None

        # Regex pattern matching
        for error_type, regexes in cls.PATTERNS:
            for pattern in regexes:
                match = re.search(pattern, combined, re.IGNORECASE)
                if match:
                    # Extract the error line
                    error_line = cls._extract_error_line(combined, pattern)
                    failing_code_line = cls._extract_failing_code_line(combined)
                    return error_type, error_line or f"Detected {error_type.value}", failing_code_line

        if exit_code != 0:
            last_line = cls._get_last_non_empty_line(stderr) or cls._get_last_non_empty_line(stdout)
            return ErrorType.LOGIC_ERROR, last_line or "Process terminated with non-zero exit code.", None

        return ErrorType.UNKNOWN_ERROR, "Unknown execution error.", None

    @staticmethod
    def _extract_error_line(text: str, pattern: str) -> Optional[str]:
        for line in reversed(text.splitlines()):
            if re.search(pattern, line, re.IGNORECASE):
                return line.strip()
        return None

    @staticmethod
    def _extract_failing_code_line(text: str) -> Optional[str]:
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if line.strip().startswith('File "') and ", line " in line:
                if i + 1 < len(lines):
                    return lines[i + 1].strip()
        return None

    @staticmethod
    def _get_last_non_empty_line(text: str) -> Optional[str]:
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        return lines[-1] if lines else None
