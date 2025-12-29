from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Any, Dict


@dataclass(frozen=True)
class AuditEvent:
    event_type: str
    payload: Dict[str, Any]


class AuditSink(Protocol):
    def emit(self, event: AuditEvent) -> None: ...
