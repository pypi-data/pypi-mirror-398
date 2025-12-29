from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from .base import AuditEvent


class JSONLAuditSink:
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

    def emit(self, event: AuditEvent) -> None:
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event.event_type,
            "payload": event.payload,
        }
        with open(self.file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
