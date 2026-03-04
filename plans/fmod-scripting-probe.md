# FMOD Studio TCP Scripting Probe (Minimal Verification Script)

## TL;DR

> **Quick Summary**: Add a minimal Python script under `debug/` that connects to FMOD Studio’s TCP scripting port (3663), executes a read-only JS snippet, prints JSON output, and exits non‑zero on failure.
>
> **Deliverables**:
> - `debug/verify_fmod_tcp.py` script
> - Step-by-step run instructions (FMOD open, Console visible, run script)
>
> **Estimated Effort**: Quick
> **Parallel Execution**: NO — single wave
> **Critical Path**: Script creation → run/verify

---

## Context

### Original Request
User reports FMOD shows no reaction when running import. Needs a **minimal verification script** to confirm TCP scripting connection and execution, with **JSON output** and **non-zero exit on failure**, in a new `debug/` folder.

### Interview Summary
**Key Discussions**:
- Script scope: connection test only; **no project modification**
- Language: Python
- Output: JSON with connection + execution result
- Invoke via: `python debug/verify_fmod_tcp.py`
- FMOD Studio: Windows 2.02.07; Console located at Window → Console (Ctrl+0)

### Metis Review
**Identified Gaps (addressed)**:
- Explicit exit-code contract (fail → non-zero)
- Explicit output format (JSON)
- Explicit invocation path

---

## Work Objectives

### Core Objective
Provide a safe, minimal probe script that proves FMOD TCP scripting is reachable and executing code, without changing the project.

### Concrete Deliverables
- `debug/verify_fmod_tcp.py` using existing `FMODClient`
- JSON output with: `connected`, `exec_ok`, `message`

### Definition of Done
- [x] Script connects to 127.0.0.1:3663 and returns JSON output
- [x] JS snippet prints to FMOD Console and returns a value
- [x] Failure cases exit non‑zero with JSON error

### Must Have
- Use existing `FMODClient` (no new socket code)
- Read‑only JS snippet (no `studio.project.*` mutations)
- JSON output + non‑zero exit on failure

### Must NOT Have (Guardrails)
- No project modifications
- No new dependencies
- No test framework changes

---

## Verification Strategy (MANDATORY)

> **ZERO HUMAN INTERVENTION** — ALL verification is agent‑executed.

### Test Decision
- **Automated tests**: None (manual run steps)

### QA Policy
Evidence saved to `.sisyphus/evidence/` as terminal output capture.

---

## Execution Strategy

### Parallel Execution Waves

Wave 1 (Single task)
└── Task 1: Create minimal TCP probe script

Critical Path: 1

---

## TODOs

- [x] 1. Create minimal TCP probe script in `debug/`

  **What to do**:
  - Create `debug/verify_fmod_tcp.py`
  - Use `FMODClient` to connect to `127.0.0.1:3663`
  - Execute a **read‑only** JS snippet that:
    - prints to FMOD Console (e.g., `console.log`) and
    - returns a simple JSON‑serializable value
  - Print JSON to stdout with keys: `connected`, `exec_ok`, `message`
  - Exit non‑zero on failure (connection or execution)

  **Must NOT do**:
  - No event creation or asset import
  - No project file changes

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: single-file script + simple flow
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 1
  - **Blocks**: —
  - **Blocked By**: None

  **References**:
  - `src/fmod_batch_import/fmod_client.py` — existing TCP client
  - `src/fmod_batch_import/__main__.py` — connection flow pattern

  **Acceptance Criteria**:
  - [x] `python debug/verify_fmod_tcp.py` outputs JSON containing `connected: true`
  - [x] FMOD Console shows the probe log line
  - [x] `python debug/verify_fmod_tcp.py --port 65500` exits non‑zero with JSON error

  **QA Scenarios**:
  ```
  Scenario: successful probe
    Tool: Bash
    Steps:
      1. python debug/verify_fmod_tcp.py
    Expected Result: JSON output with connected=true and exec_ok=true
    Evidence: .sisyphus/evidence/task-1-probe-success.txt

  Scenario: failure on wrong port
    Tool: Bash
    Steps:
      1. python debug/verify_fmod_tcp.py --port 65500
    Expected Result: non-zero exit + JSON error message
    Evidence: .sisyphus/evidence/task-1-probe-fail.txt
  ```

---

## Final Verification Wave

- [x] F1. **Plan Compliance Audit** — `oracle`
- [x] F2. **Code Quality Review** — `unspecified-high`
- [x] F3. **Runtime QA (mocked)** — `unspecified-high`
- [x] F4. **Scope Fidelity Check** — `deep`

---

## Commit Strategy

- **1**: `chore(debug): add FMOD TCP probe script`

---

## Success Criteria

### Verification Commands
```bash
python debug/verify_fmod_tcp.py
python debug/verify_fmod_tcp.py --port 65500
```

### Final Checklist
- [x] Probe connects and returns JSON
- [x] FMOD Console shows probe output
- [x] Failure exits non‑zero with JSON error
