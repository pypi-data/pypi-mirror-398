from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class DecisionResult:
    decision: str
    reasons: List[str]
    pd: float


def decision_policy(
    pd: float, *, bureau_score: Optional[int], dti: Optional[float]
) -> DecisionResult:
    reasons: List[str] = []

    if bureau_score is None or dti is None:
        return DecisionResult("MANUAL_REVIEW", ["MISSING_CRITICAL_FIELDS"], pd)

    if bureau_score < 650:
        reasons.append("LOW_BUREAU_SCORE")

    if dti > 0.55:
        reasons.append("HIGH_DTI")

    if pd >= 0.45:
        reasons.append("HIGH_PD")
        return DecisionResult("DECLINE", reasons, pd)

    if 0.35 <= pd < 0.45 or reasons:
        reasons.append("REQUIRES_HUMAN_REVIEW")
        return DecisionResult("MANUAL_REVIEW", reasons, pd)

    return DecisionResult("APPROVE", ["WITHIN_RISK_APPETITE"], pd)
