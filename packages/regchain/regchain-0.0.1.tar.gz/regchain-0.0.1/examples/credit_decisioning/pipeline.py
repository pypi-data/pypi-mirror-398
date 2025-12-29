from __future__ import annotations

import os
import pandas as pd

from regchain import Governed
from regchain.audit.jsonl import JSONLAuditSink
from regchain.policies import EscalationPolicy, ValidateSchema, ReasonPolicy, RedactPII
from regchain.utils.memo import MemoInput, render_validation_memo

from data_gen import generate_synthetic
from model import PDModel
from policy import decision_policy
from monitoring import psi, write_monitoring

OUT_DIR = os.path.join(os.path.dirname(__file__), "outputs")
os.makedirs(OUT_DIR, exist_ok=True)


def decide_engine(app: dict) -> dict:
    pd_score = app["_pd_model"].predict_pd(app)
    result = decision_policy(pd_score, bureau_score=app["bureau_score"], dti=app["dti"])
    return {
        "probability_of_default": result.pd,
        "decision": result.decision,
        "reasons": result.reasons,
    }


def main() -> None:
    audit_sink = JSONLAuditSink(os.path.join(OUT_DIR, "audit_log.jsonl"))

    base_line = generate_synthetic(n=2000, seed=42)
    model_path = os.path.join(os.path.dirname(__file__), "pd_model.joblib")
    pd_model = PDModel(
        version="0.0.1",
        feature_cols=["bureau_score", "dti", "loan_amount"],
        model_path=model_path,
    )
    metrics = pd_model.train(base_line, target_col="defaulted")
    pd_model.load()

    governed = Governed(
        decide_engine,
        pre_process_policies=[
            ValidateSchema(required=["bureau_score", "bureau_score", "dti", "loan_amount"]),
            RedactPII(pii_fields=["pan", "aadhaar", "mobile", "email"]),
        ],
        post_process_policies=[
            ReasonPolicy(),
            EscalationPolicy(pd_threshold=0.8, decision_if_high_pd="MANUAL_REVIEW"),
        ],
        audit_sink=audit_sink,
        name="CreditDecisioningEngine",
    )

    current = generate_synthetic(n=500, seed=24)
    outputs = []

    for i, row in current.iterrows():
        app = row.to_dict()
        app["application_id"] = f"APP-{i + 1:05d}"
        app["_pd_model"] = pd_model
        out = governed(app).output
        outputs.append(out)

    scored = pd.DataFrame(outputs)
    baseline_pd = base_line.apply(lambda x: pd_model.predict_pd(x.to_dict()), axis=1)
    current_pd = scored["probability_of_default"]
    psi_results = psi(baseline_pd, current_pd)

    monitoring_payload = {
        "psi_pd": psi_results,
        "decision_counts": scored["decision"].value_counts().to_dict(),
    }
    write_monitoring(os.path.join(OUT_DIR, "monitoring.json"), monitoring_payload)

    memo = MemoInput(
        model_name="Synthetic Credit Risk Model",
        model_version=pd_model.version,
        intended_use="Demostration of governed credit decisioning with audit trail, monitoring, and policies.",
        limitations=[
            "Synthetic data used; may not reflect real-world distributions.",
            "Model performance may vary on real data.",
            "Simple Feature set; real models may require more features.",
        ],
        metrics={**metrics, "psi_pd": psi_results},
        monitoring_plan=[
            "Monitor PSI monthly to detect data drift.",
            "Track decision distribution over time.",
        ],
        change_log=[
            "v0.0.1: Initial demo model + governed pipeline implementation + JSONL audit + memo"
        ],
    )
    memo_md = render_validation_memo(memo)
    with open(os.path.join(OUT_DIR, "model_validation_memo.md"), "w") as f:
        f.write(memo_md)

    print(scored.head(5).to_string(index=False))


if __name__ == "__main__":
    main()
