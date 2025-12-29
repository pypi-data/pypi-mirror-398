from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from .base import PolicyResult


@dataclass
class EscalationPolicy:
    pd_threshold: float = 0.8
    decision_if_high_pd: str = "MANUAL_REVIEW"
    name: str = "EscalationPolicy"

    def pre_process(self, input_payload: Dict[str, Any]) -> PolicyResult:
        return PolicyResult(allowed=True, actions={}, violations=[])

    def post_process(self, output_payload: Dict[str, Any]) -> PolicyResult:
        pd = output_payload.get("probability_of_default")
        if pd is not None and isinstance(pd, (float, int)) and pd >= self.pd_threshold:
            return PolicyResult(
                allowed=True,
                actions={
                    "force_decision": self.decision_if_high_pd,
                    "reason": "HIGH_PREDICTED_DEFAULT_PROBABILITY",
                },
                violations=[],
            )
        return PolicyResult(allowed=True, actions={}, violations=[])
