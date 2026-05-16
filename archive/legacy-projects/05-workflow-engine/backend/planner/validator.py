"""DAG validator — runs *before* execution. Returns structured findings."""
from __future__ import annotations

from typing import Any

from planner.dag_parser import DAG
from planner.tool_registry import ToolRegistry


class ValidationFinding:
    def __init__(self, severity: str, code: str, message: str, node_id: str | None = None) -> None:
        self.severity = severity
        self.code = code
        self.message = message
        self.node_id = node_id

    def to_dict(self) -> dict[str, Any]:
        return {"severity": self.severity, "code": self.code, "message": self.message, "node_id": self.node_id}


def validate_dag(dag: DAG, registry: ToolRegistry | None = None) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []

    # 1. Unique ids — already enforced by DAG model, but double-check
    ids = [n.id for n in dag.nodes]
    if len(set(ids)) != len(ids):
        findings.append(ValidationFinding("error", "duplicate_ids",
                                          "Node ids must be unique"))

    # 2. Tool references valid (if a registry is provided)
    if registry is not None:
        for node in dag.nodes:
            full = f"{node.tool}.{node.action}"
            if not registry.known(full):
                findings.append(ValidationFinding(
                    severity="error",
                    code="unknown_tool",
                    message=f"tool '{full}' not found in registry",
                    node_id=node.id,
                ))

    # 3. Placeholders reference upstream nodes only
    import re
    pattern = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\.")
    for node in dag.nodes:
        for v in _flatten_strings(node.params):
            for ref in pattern.findall(v):
                if ref == node.id:
                    findings.append(ValidationFinding(
                        "error", "self_reference",
                        f"node {node.id} references itself in params", node.id,
                    ))
                elif ref not in node.depends_on:
                    findings.append(ValidationFinding(
                        "error", "missing_dependency",
                        f"node {node.id} references {ref} but does not list it in depends_on",
                        node.id,
                    ))

    # 4. Approval flags on non-idempotent tools — warn if missing
    if registry is not None:
        for node in dag.nodes:
            full = f"{node.tool}.{node.action}"
            schema = next((t for t in registry.schemas() if t["name"] == full), None)
            if schema and not schema.get("idempotent") and not node.requires_approval:
                findings.append(ValidationFinding(
                    "warn", "no_approval_on_side_effect",
                    f"non-idempotent tool '{full}' has no HITL gate", node.id,
                ))

    return findings


def _flatten_strings(value: Any) -> list[str]:
    out: list[str] = []
    if isinstance(value, str):
        out.append(value)
    elif isinstance(value, dict):
        for v in value.values():
            out.extend(_flatten_strings(v))
    elif isinstance(value, list):
        for v in value:
            out.extend(_flatten_strings(v))
    return out


def has_errors(findings: list[ValidationFinding]) -> bool:
    return any(f.severity == "error" for f in findings)
