from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Any, Dict, List


@dataclass
class PolicyResult:
    allowed: bool
    actions: Dict[str, Any]
    violations: List[str]


class Policy(Protocol):
    name: str

    def pre_process(self, input_payload: Dict[str, Any]) -> PolicyResult: ...

    def post_process(self, output_payload: Dict[str, Any]) -> PolicyResult: ...
