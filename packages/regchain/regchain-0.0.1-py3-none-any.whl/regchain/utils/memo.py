from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List


@dataclass
class MemoInput:
    model_name: str
    model_version: str
    intended_use: str
    limitations: List[str]
    metrics: Dict[str, Any]
    monitoring_plan: List[str]
    change_log: List[str]


def render_validation_memo(m: MemoInput) -> str:
    lim = "\n".join([f"- {x}" for x in m.limitations])
    mon = "\n".join([f"- {x}" for x in m.monitoring_plan])
    chg = "\n".join([f"- {x}" for x in m.change_log])
    met = "\n".join([f"- **{k}**: {v}" for k, v in m.metrics.items()])

    return f"""# Model Validation Memo (Draft)

**Date:** {date.today().isoformat()}
**Model:** {m.model_name}
**Version:** {m.model_version}

## Intended Use
{m.intended_use}

## Performance Metrics
{met}

## Limitations / Assumptions
{lim}

## Monitoring Plan
{mon}

## Change Log
{chg}

> Note: Auto-generated draft for demonstration purposes.
"""
