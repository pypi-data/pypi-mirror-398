from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from regchain.audit import AuditSink, AuditEvent
from regchain.policies.base import Policy


@dataclass
class GovernedResult:
    output: Dict[str, Any]
    violations: List[str]


class Governed:
    def __init__(
        self,
        fn: Callable[[Dict[str, Any]], Dict[str, Any]],
        *,
        pre_process_policies: Optional[List[Policy]] = None,
        post_process_policies: Optional[List[Policy]] = None,
        audit_sink: Optional[AuditSink] = None,
        name: str = "GovernedFunction",
    ) -> None:
        self.fn = fn
        self.pre_process_policies = pre_process_policies or []
        self.post_process_policies = post_process_policies or []
        self.audit_sink = audit_sink
        self.name = name

    def __call__(self, input_payload: Dict[str, Any]) -> GovernedResult:
        working_input = dict(input_payload)
        all_violations: List[str] = []

        forced_decision = None
        forced_reason = None

        for policy in self.pre_process_policies:
            result = policy.pre_process(working_input)
            all_violations.extend([f"{policy.name}: {v}" for v in result.violations])

            if "redact" in result.actions:
                for k, v in result.actions["redact"].items():
                    working_input[k] = v

            if "force_decision" in result.actions:
                forced_decision = result.actions["force_decision"]

            if "reason" in result.actions:
                forced_reason = result.actions["reason"]

        self._emit("decision.request", {"name": self.name, "input": working_input})
        output = self.fn(dict(input_payload))

        if forced_decision is not None:
            output = dict(output)
            output["decision"] = forced_decision
            output.setdefault("reasons", [])
            if forced_reason is not None:
                output["reasons"].append(forced_reason)

        for policy in self.post_process_policies:
            result = policy.post_process(output)
            all_violations.extend([f"{policy.name}: {v}" for v in result.violations])

            if "force_decision" in result.actions:
                output["decision"] = result.actions["force_decision"]

            if "add_reason" in result.actions:
                output.setdefault("reasons", [])
                output["reasons"].append(result.actions["add_reason"])

        self._emit(
            "decision.response", {"name": self.name, "output": output, "violations": all_violations}
        )
        return GovernedResult(output=output, violations=all_violations)

    def _emit(self, event_type: str, payload: Dict[str, Any]) -> None:
        if self.audit_sink is None:
            return
        # Filter out non-serializable objects (like models) from payload
        filtered_payload = {}
        for key, value in payload.items():
            if key == "input" and isinstance(value, dict):
                # Filter out keys starting with underscore (convention for non-serializable objects)
                filtered_payload[key] = {k: v for k, v in value.items() if not k.startswith("_")}
            else:
                filtered_payload[key] = value
        self.audit_sink.emit(AuditEvent(event_type=event_type, payload=filtered_payload))
