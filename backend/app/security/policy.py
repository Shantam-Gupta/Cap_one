"""Static AST-based Policy Engine for Pre-Execution Security Checks."""
import ast
from dataclasses import dataclass, field
from typing import List, Optional

# pyrefly: ignore [missing-import]
from app.schemas.enums import NetworkPolicy
# pyrefly: ignore [missing-import]
from app.security.rules import FORBIDDEN_MODULES, FORBIDDEN_PATHS, SUSPICIOUS_CALLS


@dataclass
class SecurityReport:
    """Detailed verdict from security policy inspection."""
    allowed: bool
    risk_level: str  # "low", "medium", "high"
    violations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self):
        return {
            "allowed": self.allowed,
            "risk_level": self.risk_level,
            "violations": self.violations,
            "warnings": self.warnings,
        }


class SecurityPolicyEngine:
    """
    Deterministic AST Static Analyzer.
    Serves as Layer 1 of the defense-in-depth security model.
    """

    def __init__(self, network_policy: NetworkPolicy = NetworkPolicy.DISABLED):
        self.network_policy = network_policy

    def inspect_code(self, source_code: str) -> SecurityReport:
        violations: List[str] = []
        warnings: List[str] = []

        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            # Syntax errors are handled by recovery agent, not blocked as security attacks
            warnings.append(f"Source code has syntax error on line {e.lineno}: {e.msg}")
            return SecurityReport(allowed=True, risk_level="low", warnings=warnings)

        for node in ast.walk(tree):
            # 1. Check Imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mod_name = alias.name.split(".")[0]
                    if mod_name in FORBIDDEN_MODULES:
                        violations.append(f"Forbidden module imported: '{alias.name}' (line {node.lineno})")
                    if self.network_policy == NetworkPolicy.DISABLED and mod_name in {"socket", "urllib", "requests", "httpx"}:
                        violations.append(f"Network call imported while policy is DISABLED: '{alias.name}' (line {node.lineno})")

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    mod_name = node.module.split(".")[0]
                    if mod_name in FORBIDDEN_MODULES:
                        violations.append(f"Forbidden module import from: '{node.module}' (line {node.lineno})")
                    if self.network_policy == NetworkPolicy.DISABLED and mod_name in {"socket", "urllib", "requests", "httpx"}:
                        violations.append(f"Network call import from while policy is DISABLED: '{node.module}' (line {node.lineno})")

            # 2. Check Suspicious Calls
            elif isinstance(node, ast.Call):
                call_name = self._get_call_name(node.func)
                if call_name in SUSPICIOUS_CALLS:
                    violations.append(f"Prohibited function or method invocation: '{call_name}' (line {node.lineno})")

            # 3. Check String Constants for Path Traversal
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                val = node.value
                if "../" in val or "..\\" in val or val.strip() == ".." or val.endswith("/..") or val.endswith("\\.."):
                    violations.append(
                        f"Suspicious path traversal reference: '{val}' (line {node.lineno})"
                    )
                    continue

                for forbidden in FORBIDDEN_PATHS:
                    if forbidden == "..":
                        continue
                    if forbidden.lower() in val.lower():
                        violations.append(
                            f"Suspicious sensitive host directory reference: '{val}' (line {node.lineno})"
                        )
                        break

        # Determine risk level
        if violations:
            return SecurityReport(allowed=False, risk_level="high", violations=violations, warnings=warnings)
        elif warnings:
            return SecurityReport(allowed=True, risk_level="medium", violations=[], warnings=warnings)
        else:
            return SecurityReport(allowed=True, risk_level="low", violations=[], warnings=[])

    def _get_call_name(self, node: ast.AST) -> str:
        """Helper to resolve call names from AST nodes."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            val_name = self._get_call_name(node.value)
            return f"{val_name}.{node.attr}" if val_name else node.attr
        return ""
