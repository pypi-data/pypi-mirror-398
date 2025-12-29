from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Sequence

from dbl_core import DblEvent, DblEventKind, GateDecision


class Phase(str, Enum):
    EMPTY = "EMPTY"
    INTENTED = "INTENTED"
    DENIED = "DENIED"
    ALLOWED = "ALLOWED"
    EXECUTED = "EXECUTED"
    PROVEN = "PROVEN"
    INVALID = "INVALID"


class RunnerStatus(str, Enum):
    EMPTY = "EMPTY"
    INTENTED = "INTENTED"
    DENIED = "DENIED"
    ALLOWED = "ALLOWED"
    FINALIZED = "FINALIZED"
    INVALID = "INVALID"


@dataclass(frozen=True)
class State:
    phase: Phase
    runner_status: RunnerStatus
    t_index: Optional[int]
    note: str = ""


def runner_status_from_phase(phase: Phase) -> RunnerStatus:
    if phase in (Phase.EXECUTED, Phase.PROVEN):
        return RunnerStatus.FINALIZED
    if phase == Phase.EMPTY:
        return RunnerStatus.EMPTY
    if phase == Phase.INTENTED:
        return RunnerStatus.INTENTED
    if phase == Phase.DENIED:
        return RunnerStatus.DENIED
    if phase == Phase.ALLOWED:
        return RunnerStatus.ALLOWED
    return RunnerStatus.INVALID


def project_state(v: Sequence[DblEvent]) -> State:
    if len(v) == 0:
        phase = Phase.EMPTY
        return State(phase=phase, runner_status=runner_status_from_phase(phase), t_index=None, note="no events")

    last_intent: Optional[int] = None
    decision_indices: list[int] = []
    decision_outcomes: list[str] = []
    execution_indices: list[int] = []
    proof_indices: list[int] = []

    for i, event in enumerate(v):
        if event.event_kind == DblEventKind.INTENT:
            last_intent = i
            continue

        if event.event_kind == DblEventKind.DECISION:
            if last_intent is None:
                return State(Phase.INVALID, RunnerStatus.INVALID, i, "DECISION before INTENT")
            if not isinstance(event.data, GateDecision):
                return State(Phase.INVALID, RunnerStatus.INVALID, i, "DECISION missing GateDecision")
            decision_value = str(event.data.decision)
            if decision_value not in ("ALLOW", "DENY"):
                return State(Phase.INVALID, RunnerStatus.INVALID, i, "DECISION missing/invalid outcome")
            decision_indices.append(i)
            decision_outcomes.append(decision_value)
            continue

        if event.event_kind == DblEventKind.EXECUTION:
            if last_intent is None:
                return State(Phase.INVALID, RunnerStatus.INVALID, i, "EXECUTION before INTENT")
            execution_indices.append(i)
            continue

        if event.event_kind == DblEventKind.PROOF:
            if last_intent is None:
                return State(Phase.INVALID, RunnerStatus.INVALID, i, "PROOF before INTENT")
            proof_indices.append(i)
            continue
        return State(Phase.INVALID, RunnerStatus.INVALID, i, f"unknown event kind: {event.event_kind!r}")

    t_last = len(v) - 1

    if last_intent is None:
        phase = Phase.INVALID
        return State(phase=phase, runner_status=runner_status_from_phase(phase), t_index=t_last, note="no INTENT in stream")

    effective_decision_idx: Optional[int] = None
    effective_decision_outcome: Optional[str] = None
    for idx, outcome in zip(decision_indices, decision_outcomes):
        if idx > last_intent:
            effective_decision_idx = idx
            effective_decision_outcome = outcome

    if effective_decision_idx is None:
        if any(idx > last_intent for idx in execution_indices):
            phase = Phase.INVALID
            return State(phase=phase, runner_status=runner_status_from_phase(phase), t_index=t_last, note="EXECUTION without effective ALLOW")
        phase = Phase.INTENTED
        return State(phase=phase, runner_status=runner_status_from_phase(phase), t_index=t_last, note="awaiting decision")

    if effective_decision_outcome == "DENY":
        if any(idx > effective_decision_idx for idx in execution_indices):
            phase = Phase.INVALID
            return State(phase=phase, runner_status=runner_status_from_phase(phase), t_index=t_last, note="EXECUTION after final DENY")
        phase = Phase.DENIED
        return State(phase=phase, runner_status=runner_status_from_phase(phase), t_index=t_last, note="denied by last decision")

    if effective_decision_outcome == "ALLOW":
        reachable_executions = [idx for idx in execution_indices if idx > effective_decision_idx]
        if not reachable_executions:
            phase = Phase.ALLOWED
            return State(phase=phase, runner_status=runner_status_from_phase(phase), t_index=t_last, note="allowed by last decision")
        last_execution = max(reachable_executions)
        reachable_proofs = [idx for idx in proof_indices if idx > last_execution]
        if reachable_proofs:
            phase = Phase.PROVEN
            return State(phase=phase, runner_status=runner_status_from_phase(phase), t_index=t_last, note="proof observed")
        phase = Phase.EXECUTED
        return State(phase=phase, runner_status=runner_status_from_phase(phase), t_index=t_last, note="execution observed")

    phase = Phase.INVALID
    return State(phase=phase, runner_status=runner_status_from_phase(phase), t_index=t_last, note="unclassified")
