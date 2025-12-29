from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from .base import PolicyResult


@dataclass
class ReasonPolicy:
    name: str = "ReasonPolicy"

    def pre_process(self, input_payload: Dict[str, Any]) -> PolicyResult:
        return PolicyResult(allowed=True, actions={}, violations=[])

    def post_process(self, output_payload: Dict[str, Any]) -> PolicyResult:
        reasons = output_payload.get("reasons")
        if not reasons or not isinstance(reasons, list):
            return PolicyResult(allowed=False, actions={}, violations=["missing_reason_codes"])
        return PolicyResult(allowed=True, actions={}, violations=[])
