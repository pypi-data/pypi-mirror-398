# DBL Main

DBL Main provides a deterministic projection of the dbl-core event stream V into a finite state model. It does not execute tasks.

## Scope
- Pure state projection from V (append-only event stream).
- Deterministic status evaluation based only on event ordering and DECISION outcomes.
- No policy engine, no kernel runtime, no IO side effects.
dbl-main exports projection primitives only.

## Contract
- docs/dbl_main_contract.md

## Install

```bash
pip install dbl-main
```

Requires `dbl-core>=0.3.0`, Python 3.11+.

## Usage

```python
from dbl_core import DblEvent, DblEventKind, GateDecision
from dbl_main import Phase, RunnerStatus, project_state

v = [
    DblEvent(DblEventKind.INTENT, correlation_id="c1", data={"psi": "x"}),
    DblEvent(DblEventKind.DECISION, correlation_id="c1", data=GateDecision("ALLOW", "ok")),
    DblEvent(DblEventKind.EXECUTION, correlation_id="c1", data={"trace": {}, "trace_digest": "..." }),
    DblEvent(DblEventKind.PROOF, correlation_id="c1", data={"proof": "p1"}),
]

state = project_state(v)
assert state.phase in (Phase.EXECUTED, Phase.PROVEN)
assert state.runner_status == RunnerStatus.FINALIZED
```

## License

MIT License. See LICENSE.
