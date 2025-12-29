from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from .base import PolicyResult


@dataclass
class RedactPII:
    pii_fields: List[str]
    mask: str = "***REDACTED***"
    name: str = "RedactPII"

    def pre_process(self, input_payload: Dict[str, Any]) -> PolicyResult:
        redacted = {
            k: self.mask
            for k in self.pii_fields
            if k in input_payload and input_payload[k] is not None
        }
        return PolicyResult(allowed=True, actions={"redact": redacted}, violations=[])

    def post_process(self, output_payload: Dict[str, Any]) -> PolicyResult:
        return PolicyResult(allowed=True, actions={}, violations={})
