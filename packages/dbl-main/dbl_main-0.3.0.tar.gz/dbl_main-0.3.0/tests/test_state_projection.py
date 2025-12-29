from __future__ import annotations

import pytest

from dbl_core import DblEvent, DblEventKind, GateDecision
from dbl_core.events import trace_core_digest
from dbl_main import Phase, RunnerStatus, project_state, runner_status_from_phase


def test_empty_stream():
    state = project_state([])
    assert state.phase == Phase.EMPTY
    assert state.runner_status == RunnerStatus.EMPTY
    assert state.t_index is None


def test_intent_then_no_decision():
    v = [
        DblEvent(DblEventKind.INTENT, correlation_id="c1", data={"psi": "x"}),
    ]
    state = project_state(v)
    assert state.phase == Phase.INTENTED
    assert state.runner_status == RunnerStatus.INTENTED


def test_deny_path():
    v = [
        DblEvent(DblEventKind.INTENT, correlation_id="c1", data={"psi": "x"}),
        DblEvent(DblEventKind.DECISION, correlation_id="c1", data=GateDecision("DENY", "blocked")),
    ]
    state = project_state(v)
    assert state.phase == Phase.DENIED
    assert state.runner_status == RunnerStatus.DENIED


def test_allow_then_no_execution():
    v = [
        DblEvent(DblEventKind.INTENT, correlation_id="c1", data={"psi": "x"}),
        DblEvent(DblEventKind.DECISION, correlation_id="c1", data=GateDecision("ALLOW", "ok")),
    ]
    state = project_state(v)
    assert state.phase == Phase.ALLOWED
    assert state.runner_status == RunnerStatus.ALLOWED


def test_allow_then_execution():
    trace = {
        "psi": {"psi_type": "x", "name": "y", "metadata": {}},
        "success": True,
        "failure_code": "OK",
        "exception_type": None,
    }
    trace_digest = trace_core_digest(trace)
    v = [
        DblEvent(DblEventKind.INTENT, correlation_id="c1", data={"psi": "x"}),
        DblEvent(DblEventKind.DECISION, correlation_id="c1", data=GateDecision("ALLOW", "ok")),
        DblEvent(DblEventKind.EXECUTION, correlation_id="c1", data={"trace": trace, "trace_digest": trace_digest}),
    ]
    state = project_state(v)
    assert state.phase == Phase.EXECUTED
    assert state.runner_status == RunnerStatus.FINALIZED


def test_allow_then_execution_then_proof():
    trace = {
        "psi": {"psi_type": "x", "name": "y", "metadata": {}},
        "success": True,
        "failure_code": "OK",
        "exception_type": None,
    }
    trace_digest = trace_core_digest(trace)
    v = [
        DblEvent(DblEventKind.INTENT, correlation_id="c1", data={"psi": "x"}),
        DblEvent(DblEventKind.DECISION, correlation_id="c1", data=GateDecision("ALLOW", "ok")),
        DblEvent(DblEventKind.EXECUTION, correlation_id="c1", data={"trace": trace, "trace_digest": trace_digest}),
        DblEvent(DblEventKind.PROOF, correlation_id="c1", data={"proof": "p1"}),
    ]
    state = project_state(v)
    assert state.phase == Phase.PROVEN
    assert state.runner_status == RunnerStatus.FINALIZED


@pytest.mark.parametrize(
    "v, note",
    [
        ([DblEvent(DblEventKind.DECISION, correlation_id="c1", data=GateDecision("ALLOW", "ok"))], "DECISION before INTENT"),
        ([DblEvent(DblEventKind.INTENT, correlation_id="c1", data={"psi": "x"}), DblEvent(DblEventKind.EXECUTION, correlation_id="c1", data={"trace": {"psi": {"psi_type": "x", "name": "y", "metadata": {}}, "success": True, "failure_code": "OK", "exception_type": None}, "trace_digest": trace_core_digest({"psi": {"psi_type": "x", "name": "y", "metadata": {}}, "success": True, "failure_code": "OK", "exception_type": None})})], "EXECUTION without effective ALLOW"),
        ([DblEvent(DblEventKind.INTENT, correlation_id="c1", data={"psi": "x"}), DblEvent(DblEventKind.DECISION, correlation_id="c1", data={"decision": "ALLOW"})], "DECISION missing GateDecision"),
    ],
)
def test_invalid_sequences(v, note):
    state = project_state(v)
    assert state.phase == Phase.INVALID
    assert note in state.note


def test_last_decision_wins():
    v = [
        DblEvent(DblEventKind.INTENT, correlation_id="c1", data={"psi": "x"}),
        DblEvent(DblEventKind.DECISION, correlation_id="c1", data=GateDecision("DENY", "blocked")),
        DblEvent(DblEventKind.DECISION, correlation_id="c1", data=GateDecision("ALLOW", "ok")),
    ]
    state = project_state(v)
    assert state.phase == Phase.ALLOWED


def test_allow_then_execution_then_deny_is_denied():
    trace = {
        "psi": {"psi_type": "x", "name": "y", "metadata": {}},
        "success": True,
        "failure_code": "OK",
        "exception_type": None,
    }
    trace_digest = trace_core_digest(trace)
    v = [
        DblEvent(DblEventKind.INTENT, correlation_id="c1", data={"psi": "x"}),
        DblEvent(DblEventKind.DECISION, correlation_id="c1", data=GateDecision("ALLOW", "ok")),
        DblEvent(DblEventKind.EXECUTION, correlation_id="c1", data={"trace": trace, "trace_digest": trace_digest}),
        DblEvent(DblEventKind.DECISION, correlation_id="c1", data=GateDecision("DENY", "blocked")),
    ]
    state = project_state(v)
    assert state.phase == Phase.DENIED
    assert state.runner_status == RunnerStatus.DENIED


def test_deny_then_allow_then_execution_is_finalized():
    trace = {
        "psi": {"psi_type": "x", "name": "y", "metadata": {}},
        "success": True,
        "failure_code": "OK",
        "exception_type": None,
    }
    trace_digest = trace_core_digest(trace)
    v = [
        DblEvent(DblEventKind.INTENT, correlation_id="c1", data={"psi": "x"}),
        DblEvent(DblEventKind.DECISION, correlation_id="c1", data=GateDecision("DENY", "blocked")),
        DblEvent(DblEventKind.DECISION, correlation_id="c1", data=GateDecision("ALLOW", "ok")),
        DblEvent(DblEventKind.EXECUTION, correlation_id="c1", data={"trace": trace, "trace_digest": trace_digest}),
    ]
    state = project_state(v)
    assert state.phase == Phase.EXECUTED
    assert state.runner_status == RunnerStatus.FINALIZED


def test_intent_after_decision_requires_new_decision():
    v = [
        DblEvent(DblEventKind.INTENT, correlation_id="c1", data={"psi": "x"}),
        DblEvent(DblEventKind.DECISION, correlation_id="c1", data=GateDecision("ALLOW", "ok")),
        DblEvent(DblEventKind.INTENT, correlation_id="c1", data={"psi": "x"}),
    ]
    state = project_state(v)
    assert state.phase == Phase.INTENTED


def test_allow_then_execution_then_intent_is_intented():
    trace = {
        "psi": {"psi_type": "x", "name": "y", "metadata": {}},
        "success": True,
        "failure_code": "OK",
        "exception_type": None,
    }
    trace_digest = trace_core_digest(trace)
    v = [
        DblEvent(DblEventKind.INTENT, correlation_id="c1", data={"psi": "x"}),
        DblEvent(DblEventKind.DECISION, correlation_id="c1", data=GateDecision("ALLOW", "ok")),
        DblEvent(DblEventKind.EXECUTION, correlation_id="c1", data={"trace": trace, "trace_digest": trace_digest}),
        DblEvent(DblEventKind.INTENT, correlation_id="c1", data={"psi": "x"}),
    ]
    state = project_state(v)
    assert state.phase == Phase.INTENTED


def test_execution_after_final_deny_is_invalid():
    trace = {
        "psi": {"psi_type": "x", "name": "y", "metadata": {}},
        "success": True,
        "failure_code": "OK",
        "exception_type": None,
    }
    trace_digest = trace_core_digest(trace)
    v = [
        DblEvent(DblEventKind.INTENT, correlation_id="c1", data={"psi": "x"}),
        DblEvent(DblEventKind.DECISION, correlation_id="c1", data=GateDecision("ALLOW", "ok")),
        DblEvent(DblEventKind.EXECUTION, correlation_id="c1", data={"trace": trace, "trace_digest": trace_digest}),
        DblEvent(DblEventKind.DECISION, correlation_id="c1", data=GateDecision("DENY", "blocked")),
        DblEvent(DblEventKind.EXECUTION, correlation_id="c1", data={"trace": trace, "trace_digest": trace_digest}),
    ]
    state = project_state(v)
    assert state.phase == Phase.INVALID


def test_proof_before_pivot_is_ignored():
    v = [
        DblEvent(DblEventKind.INTENT, correlation_id="c1", data={"psi": "x"}),
        DblEvent(DblEventKind.PROOF, correlation_id="c1", data={"proof": "p1"}),
    ]
    state = project_state(v)
    assert state.phase == Phase.INTENTED


def test_proof_without_execution_does_not_advance():
    v = [
        DblEvent(DblEventKind.INTENT, correlation_id="c1", data={"psi": "x"}),
        DblEvent(DblEventKind.DECISION, correlation_id="c1", data=GateDecision("ALLOW", "ok")),
        DblEvent(DblEventKind.PROOF, correlation_id="c1", data={"proof": "p1"}),
    ]
    state = project_state(v)
    assert state.phase == Phase.ALLOWED


def test_projection_ignores_correlation_id():
    v = [
        DblEvent(DblEventKind.INTENT, correlation_id="c1", data={"psi": "x"}),
        DblEvent(DblEventKind.DECISION, correlation_id="c1", data=GateDecision("ALLOW", "ok")),
        DblEvent(DblEventKind.INTENT, correlation_id="c2", data={"psi": "y"}),
    ]
    state = project_state(v)
    assert state.phase == Phase.INTENTED


def test_unknown_event_kind_is_invalid():
    v = [
        DblEvent(DblEventKind.INTENT, correlation_id="c1", data={"psi": "x"}),
        DblEvent("UNKNOWN", correlation_id="c1", data={}),
    ]
    state = project_state(v)
    assert state.phase == Phase.INVALID
    assert "unknown event kind" in state.note


def test_runner_status_finalized_mapping():
    trace = {
        "psi": {"psi_type": "x", "name": "y", "metadata": {}},
        "success": True,
        "failure_code": "OK",
        "exception_type": None,
    }
    trace_digest = trace_core_digest(trace)
    executed_state = project_state(
        [
            DblEvent(DblEventKind.INTENT, correlation_id="c1", data={"psi": "x"}),
            DblEvent(DblEventKind.DECISION, correlation_id="c1", data=GateDecision("ALLOW", "ok")),
            DblEvent(DblEventKind.EXECUTION, correlation_id="c1", data={"trace": trace, "trace_digest": trace_digest}),
        ]
    )
    proven_state = project_state(
        [
            DblEvent(DblEventKind.INTENT, correlation_id="c1", data={"psi": "x"}),
            DblEvent(DblEventKind.DECISION, correlation_id="c1", data=GateDecision("ALLOW", "ok")),
            DblEvent(DblEventKind.EXECUTION, correlation_id="c1", data={"trace": trace, "trace_digest": trace_digest}),
            DblEvent(DblEventKind.PROOF, correlation_id="c1", data={"proof": "p1"}),
        ]
    )
    assert runner_status_from_phase(executed_state.phase) == RunnerStatus.FINALIZED
    assert runner_status_from_phase(proven_state.phase) == RunnerStatus.FINALIZED

    other_states = [
        project_state([]),
        project_state([DblEvent(DblEventKind.INTENT, correlation_id="c1", data={"psi": "x"})]),
        project_state([DblEvent(DblEventKind.INTENT, correlation_id="c1", data={"psi": "x"}), DblEvent(DblEventKind.DECISION, correlation_id="c1", data=GateDecision("DENY", "blocked"))]),
        project_state([DblEvent(DblEventKind.INTENT, correlation_id="c1", data={"psi": "x"}), DblEvent(DblEventKind.DECISION, correlation_id="c1", data=GateDecision("ALLOW", "ok"))]),
        project_state([DblEvent(DblEventKind.DECISION, correlation_id="c1", data=GateDecision("ALLOW", "ok"))]),
    ]
    assert all(runner_status_from_phase(state.phase) != RunnerStatus.FINALIZED for state in other_states)
