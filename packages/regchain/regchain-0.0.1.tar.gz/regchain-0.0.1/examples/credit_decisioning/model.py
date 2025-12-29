from __future__ import annotations

from dataclasses import dataclass

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score


@dataclass
class PDModel:
    version: str
    feature_cols: list[str]
    model_path: str

    def train(self, df: pd.DataFrame, target_col: str) -> dict:
        X = df[self.feature_cols].values
        y = df[target_col].values

        clf = LogisticRegression(max_iter=500)
        clf.fit(X, y)

        pd_scores = clf.predict_proba(X)[:, 1]
        auc = float(roc_auc_score(y, pd_scores))

        joblib.dump(clf, self.model_path)
        return {"auc": auc}

    def load(self) -> None:
        self._clf = joblib.load(self.model_path)

    def predict_pd(self, row: dict) -> float:
        X = np.array([[row[c] for c in self.feature_cols]], dtype=float)
        return float(self._clf.predict_proba(X)[0, 1])
