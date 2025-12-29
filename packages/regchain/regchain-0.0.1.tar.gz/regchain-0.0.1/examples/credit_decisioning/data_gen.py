from __future__ import annotations

import numpy as np
import pandas as pd


def generate_synthetic(n: int = 2000, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    # Create more diverse profiles with wider distributions
    # Mix of good, medium, and risky applicants
    segment = rng.choice(["good", "medium", "risky"], size=n, p=[0.3, 0.4, 0.3])

    bureau = np.zeros(n, dtype=int)
    dti = np.zeros(n, dtype=float)

    # Good credit profiles - higher bureau scores, lower DTI
    good_mask = segment == "good"
    bureau[good_mask] = rng.integers(700, 850, size=good_mask.sum())
    dti[good_mask] = np.clip(rng.normal(0.25, 0.10, size=good_mask.sum()), 0.05, 0.50)

    # Medium credit profiles - average scores and DTI
    medium_mask = segment == "medium"
    bureau[medium_mask] = rng.integers(620, 720, size=medium_mask.sum())
    dti[medium_mask] = np.clip(rng.normal(0.40, 0.12, size=medium_mask.sum()), 0.15, 0.65)

    # Risky credit profiles - lower scores, higher DTI
    risky_mask = segment == "risky"
    bureau[risky_mask] = rng.integers(550, 650, size=risky_mask.sum())
    dti[risky_mask] = np.clip(rng.normal(0.55, 0.15, size=risky_mask.sum()), 0.35, 0.95)

    loan_amount = rng.integers(50_000, 2_000_000, size=n)

    score = -0.015 * (bureau - 700) + 5.0 * (dti - 0.35) + 0.0000008 * (loan_amount - 500_000)
    pd_true = 1 / (1 + np.exp(-score))
    y = rng.binomial(1, np.clip(pd_true, 0.01, 0.50))

    return pd.DataFrame(
        {
            "bureau_score": bureau.astype(int),
            "dti": dti.astype(float),
            "loan_amount": loan_amount.astype(float),
            "defaulted": y.astype(int),
        }
    )
