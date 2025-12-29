from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from .base import PolicyResult


@dataclass
class ValidateSchema:
    required: List[str]
    name: str = "ValidateSchema"

    def pre_process(self, input_payload: Dict[str, Any]) -> PolicyResult:
        violations = []
        for field in self.required:
            if field not in input_payload:
                violations[field] = "Field is required but missing."
        if violations:
            return PolicyResult(
                allowed=False,
                actions={"force_decision": "MANUAL_REVIEW", "reason": "MISSING_FIELDS"},
                violations=[f"missing field: {field}" for field in violations],
            )
        return PolicyResult(allowed=True, actions={}, violations=[])

    def post_process(self, output_payload: Dict[str, Any]) -> PolicyResult:
        return PolicyResult(allowed=True, actions={}, violations={})
