# DBL Core

DBL Core is a deterministic event substrate for the Deterministic Boundary Layer (DBL). It records intent, decisions, and executions as a single ordered stream.

## Scope
- Single-stream event model with deterministic t_index.
- Canonical serialization and digest for events and behavior logs.
- Gate decision events (ALLOW or DENY) as explicit Deltas.
- Embeds kernel ExecutionTrace as immutable facts.

## Non-Goals
- No policy engine or templates.
- No execution of user tasks.
- No orchestration, UX flows, or intelligence.
- No time, randomness, or I/O side effects.

## Contract
- docs/dbl_contract.md

## Install

```bash
pip install dbl-core
```
Requires kl-kernel-logic>=0.5.0 and Python 3.11+.

## Public API
- DblEvent, DblEventKind
- BehaviorV
- GateDecision
- normalize_trace

## Ordering
Ordering is derived from t_index (position in V). Timestamps and runtime fields are observational only.

## License
MIT License. See LICENSE.
