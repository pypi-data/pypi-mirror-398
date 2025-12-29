from __future__ import annotations

import json
from typing import Dict

import numpy as np
import pandas as pd


def psi(expected: pd.Series, actual: pd.Series, buckets: int = 10) -> float:
    eps = 1e-6
    quantiles = np.linspace(0, 1, buckets + 1)
    cuts = expected.quantile(quantiles).values
    cuts[0] = -np.inf
    cuts[-1] = np.inf

    exp_bins = pd.cut(expected, bins=cuts).value_counts(normalize=True).sort_index()
    act_bins = pd.cut(actual, bins=cuts).value_counts(normalize=True).sort_index()

    return float(
        ((act_bins + eps - (exp_bins + eps)) * np.log((act_bins + eps) / (exp_bins + eps))).sum()
    )


def write_monitoring(path: str, payload: Dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
