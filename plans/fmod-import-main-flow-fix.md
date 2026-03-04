# FMOD Import Main Flow Fix (Create‑Only + GUID + Verification)

## TL;DR

> **Quick Summary**: Fix the main FMOD import pipeline to **execute JS**, **create events without template cloning**, **resolve event paths to GUIDs**, and **verify event/track/sound/bus/bank** per row. Failures should mark rows as failed and continue. Use TDD.
>
> **Deliverables**:
> - Orchestrator executes FMOD JS per row (no TODO)
> - Event creation uses `create → addGroupTrack → addSound`
> - Path→GUID resolution from FMOD Metadata for event paths
> - Strict post‑execution verification and structured error reporting

---

## Context

### Original Request
User wants to **re‑locate root causes** and then fix main import flow. Decisions:
- Remove template cloning entirely (create‑only)
- Resolve event paths to GUIDs
- Add strict post‑execution verification
- TDD
- If event exists → skip; failure → mark failed & continue

### Key Findings from Review
- `_process_row()` in `orchestrator.py` **does not execute FMOD JS** (TODO only)
- `Event.clone()` is not supported in FMOD 2.02; official API is create + addGroupTrack/addSound
- ToMany relationships require `relationships.X.add()` (no assignment)
- FMOD `project.lookup` is more reliable with GUIDs

---

## Work Objectives

### Core Objective
Make the main pipeline **actually import** by executing FMOD JS that uses official APIs, with GUID resolution and strict verification.

### Must Have
- No template cloning
- Event creation via `project.create('Event')` + `addGroupTrack` + `addSound`
- Path→GUID resolver from project `Metadata/` for event paths
- Per‑row JS execution and structured success/failure handling
- Strict verification: event exists + sound bound + bus/bank assigned

### Must NOT Have
- No UI‑dependent duplication
- No silent success
- No changes to CSV schema

---

## Verification Strategy

- **Test Strategy**: TDD
- **Success condition**: strict verification per row

---

## Execution Strategy

Wave 1 — Core Flow (TDD)
1. Implement path→GUID resolver
2. Implement create‑only JS builder (track + sound)
3. Execute JS in orchestrator with strict verification

Wave 2 — Validation + Error Handling (TDD)
4. Post‑execution verification logic (event/bus/bank)
5. Error handling + skip behavior for existing events

---

## TODOs

- [x] 1. **Path→GUID Resolver (TDD)**
  - Build a resolver using `Metadata/Workspace.xml`, `Metadata/EventFolder/*.xml`, `Metadata/Event/*.xml`
  - Resolve `event:/A/B/C` → `{GUID}`
  - Unit tests for valid path + missing path

- [x] 2. **Create‑Only Import JS Builder (TDD)**
  - Build JS using `project.create('Event')`, `event.addGroupTrack`, `track.addSound`
  - Bind audio file using `sound.audioFile` or `sound.sound`
  - Assign bus + bank using lookup + assignment
  - Tests ensure correct JS content (no template clone)

- [x] 3. **Orchestrator Executes JS (TDD)**
  - Remove TODO and execute JS per row
  - Parse FMOD response (`out(): {...}` JSON)
  - Mark rows failed on error but continue

- [x] 4. **Strict Verification (TDD)**
  - Verify event created, sound bound, bus assigned, bank assigned
  - If verification fails → mark failed with reason
  - Tests for verification failures

- [x] 5. **Skip Existing Events (TDD)**
  - If event path exists (resolved GUID), skip row
  - Log skip reason and continue

---

## Final Verification Wave

- [x] F1. Plan Compliance Audit
- [x] F2. Code Quality Review
- [x] F3. Runtime QA (mocked)
- [x] F4. Scope Fidelity Check

---

## Success Criteria

- [x] FMOD JS executed per row
- [x] Events created without template cloning
- [x] GUID resolution works for event paths
- [x] Strict verification passes when import succeeds
- [x] Failures logged and batch continues
