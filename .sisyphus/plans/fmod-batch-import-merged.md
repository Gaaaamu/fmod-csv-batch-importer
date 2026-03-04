# FMOD Batch Import (Merged) — Implementation Plan

## TL;DR

> **Quick Summary**: Merge the existing FMOD batch-import plans into one evidence-backed implementation for FMOD Studio 2.02.07, rebuilt from scratch in this workspace, using create-only event creation, strict CSV + audio rules, and a double‑click `.bat` entry with no CLI input.
>
> **Deliverables**:
> - Python package implementing CSV-driven FMOD import (create-only)
> - FMOD TCP probe + model discovery utilities
> - GUI selection flow + double‑click `.bat` launcher
> - Markdown log output (next to CSV)
> - Automated tests (hybrid TDD + integration)
>
> **Estimated Effort**: Large
> **Parallel Execution**: YES — 3 waves
> **Critical Path**: TCP client → discovery mapping → create-only JS builder → orchestrator → GUI/.bat → integration tests

---

## Context

### Original Request
合并现有 5 份 FMOD 导入计划为一个完整实施计划，**无猜测**，所有技术依据来自官方文档（社区仓库仅参考）。创建-only 方式导入，CSV 固定 5 字段，严格音频匹配规则。提供 **双击 `.bat`** 入口，**不需要 CLI 输入**，输出 Markdown 日志到 CSV 同目录。按“末端→前端”分步测试流程，保证流程逐步打通。

### Interview Summary
**Key Decisions**:
- FMOD Studio 版本固定为 **2.02.07**
- **Create-only**（不使用模板克隆）
- CSV 固定 5 字段：`audio_path, event_path, asset_path, bus_path, bank_name`
- 音频匹配：仅文件名 / 无扩展名匹配 / 递归 / 大小写敏感 / 重名取首并警告
- 自动化测试必须包含（纯逻辑 TDD + FMOD 联调 Tests-after）
- 入口：双击 `.bat`，GUI 选择文件，不要求命令行输入
- 输出：Markdown 日志固定在 CSV 同目录
- 外部仓库仅参考；可复用函数需合法可靠

**Research Findings**:
- 已获取官方文档证据：Project / Workspace / Event / Track / Sound / Folder / ManagedObject / Assets / Scripting Terminal
- Bank / MixerStrip 通过用户截图补证据
- 参考仓库：
  - synnys/fmod-bulk-importer（JS 脚本 + importAudioFile + addGroupTrack + addSound）
  - 8ude/FMOD-Audio-Importer（C# Telnet + JS）
  - momnus/FmodImporter（C# Telnet + 批量导入逻辑）

---

## Work Objectives

### Core Objective
在当前工作区从零构建一个**可双击运行**的 FMOD 批量导入工具，基于官方 2.02.07 Scripting API，完成 CSV 驱动音频导入、事件创建、bus/bank 绑定与日志输出，并通过自动化测试 + 分步流程验证。

### Concrete Deliverables
- `fmod_batch_import/` 包 + `debug/` 工具脚本
- `.bat` 启动脚本（无 CLI 输入）
- 自动化测试与样例夹具
- Markdown 导入日志（与 CSV 同目录）

### Definition of Done
- [ ] `.bat` 双击后可完成 CSV 驱动导入（无需 CLI 输入）
- [ ] Markdown 日志生成于 CSV 同目录，包含逐行结果与汇总
- [ ] pytest 通过（纯逻辑 TDD + FMOD 联调 Tests-after）
- [ ] 分步流程按“末端→前端”验证通过

### Must Have
- Create-only 事件创建（禁止模板克隆）
- CSV 5 字段固定且严格校验
- 严格音频匹配规则（大小写敏感、递归、重名警告）
- TCP 3663 脚本执行与结果解析

### Must NOT Have (Guardrails)
- 不使用模板克隆（`Event.clone` 等）
- 不新增 CSV 字段或扩展 schema
- 不要求用户在命令行输入参数
- 不自动创建不存在的 bus/bank（缺失即记录并跳过）
- 不依赖未被官方文档证实的 API

---

## Verification Strategy

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed.

### Test Decision
- **Infrastructure**: pytest
- **Automated tests**: **Hybrid** — 纯逻辑 TDD + FMOD 联调 Tests-after

### QA Policy
每个任务必须附带 2 个 QA 场景（成功 + 失败/边界），并输出证据文件到 `.sisyphus/evidence/`。
为保证**无人工介入**，GUI 流程需提供**测试模式**（例如环境变量/配置文件）以便自动化运行；正式用户仍通过 GUI 选择文件。

### Stepwise Flow (End → Start)
1) **Audio import** → 2) **Event creation** → 3) **Event configuration** → 4) **CSV mapping & orchestration**

---

## Execution Strategy

### Parallel Execution Waves

Wave 1 (Foundation — pure logic + scaffolding):
├── Task 1: Project scaffolding + pytest config
├── Task 2: CSV schema + validation
├── Task 3: Audio resolver (strict rules)
├── Task 4: Path normalization + mapping logic
└── Task 5: Markdown log builder + summary stats

Wave 2 (FMOD integration foundations):
├── Task 6: FMOD TCP client + probe script
├── Task 7: ManagedObject discovery mapping (relationships/properties)
├── Task 8: Create-only JS builder (event/track/sound)
├── Task 9: Audio import + asset folder routing
└── Task 10: Bus/Bank lookup + relationship assignment

Wave 3 (End-to-end wiring + UX + tests):
├── Task 11: Orchestrator (row-by-row execution + error handling)
├── Task 12: GUI dialog flow + FMOD launch/reconnect
├── Task 13: .bat entrypoint (no CLI input)
├── Task 14: Markdown report integration + export
└── Task 15: Stepwise integration tests & evidence

Critical Path: 6 → 7 → 8 → 11 → 12 → 13 → 15

### Dependency Matrix (all tasks)

- **1** → 2,3,4,5,6,12
- **2** → 4,11
- **3** → 9,11,15
- **4** → 8,11
- **5** → 11,14
- **6** → 7,8,9,11,15
- **7** → 8,9,10,11
- **8** → 11
- **9** → 11
- **10** → 11
- **11** → 14,15
- **12** → 13
- **13** → 15
- **14** → 15
- **15** → Final Verification

### Agent Dispatch Summary

- **Wave 1**: T1–T5 → `quick`/`unspecified-low`
- **Wave 2**: T6–T10 → `unspecified-high`
- **Wave 3**: T11/T15 → `deep`; T12 → `unspecified-low`; T13–T14 → `quick`

---

## TODOs

- [x] 1. Scaffold project structure + pytest configuration

  **What to do**:
  - Create Python package layout: `fmod_batch_import/`, `debug/`, `tests/`
  - Add pytest configuration (pyproject/pytest.ini) and base test utilities
  - Add minimal sample assets folder + sample CSV fixture directory (no binary commits yet)

  **Must NOT do**:
  - Do not add runtime dependencies beyond stdlib + pytest
  - Do not introduce CLI-only entry points

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: small scaffolding + config wiring
  - **Skills**: `[]`
  - **Skills Evaluated but Omitted**:
    - `playwright`: no browser/UI automation needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (Tasks 1–5)
  - **Blocks**: Tasks 2–15
  - **Blocked By**: None

  **References**:
  - Pattern References: None (greenfield)
  - External References: https://docs.pytest.org/ (pytest config patterns)

  **Acceptance Criteria**:
  - [ ] `python -m pytest --collect-only` succeeds
  - [ ] `fmod_batch_import/`, `debug/`, `tests/` folders exist

  **QA Scenarios**:
  ```
  Scenario: Pytest can collect tests
    Tool: Bash
    Steps:
      1. Run: python -m pytest --collect-only
    Expected Result: Exit code 0; collection output includes tests/ folder
    Evidence: .sisyphus/evidence/task-1-pytest-collect.txt

  Scenario: Package layout exists
    Tool: Bash
    Steps:
      1. Run: python - <<'PY'
         import os; print(all(os.path.isdir(p) for p in ['fmod_batch_import','debug','tests']))
         PY
    Expected Result: Output `True`
    Evidence: .sisyphus/evidence/task-1-layout.txt
  ```

- [x] 2. CSV schema parsing + validation (TDD)

  **What to do**:
  - Implement CSV reader enforcing fixed 5 columns: `audio_path, event_path, asset_path, bus_path, bank_name`
  - Handle UTF‑8 BOM, empty lines, trailing commas
  - Return structured rows with row index + normalized string fields

  **Must NOT do**:
  - Do not accept extra columns
  - Do not infer defaults beyond empty-string normalization

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: isolated parsing + tests
  - **Skills**: `[]`
  - **Skills Evaluated but Omitted**:
    - `playwright`: no UI

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (Tasks 1–5)
  - **Blocks**: Tasks 11–15
  - **Blocked By**: Task 1

  **References**:
  - Pattern References: None (greenfield)
  - External References: Python csv module docs

  **Acceptance Criteria**:
  - [ ] pytest: valid CSV parses into row objects with correct fields
  - [ ] pytest: missing header or extra column → validation error

  **QA Scenarios**:
  ```
  Scenario: Valid CSV parses
    Tool: Bash
    Steps:
      1. Run: python -m pytest tests/test_csv_parser.py -k valid
    Expected Result: 1+ tests pass, exit code 0
    Evidence: .sisyphus/evidence/task-2-csv-valid.txt

  Scenario: Invalid CSV rejected
    Tool: Bash
    Steps:
      1. Run: python -m pytest tests/test_csv_parser.py -k invalid
    Expected Result: 1+ tests pass, exit code 0
    Evidence: .sisyphus/evidence/task-2-csv-invalid.txt
  ```

- [x] 3. Audio resolver with strict matching rules (TDD)

  **What to do**:
  - Implement audio resolution using strict rules:
    - filename-only match (no subpath in CSV)
    - extensionless match against allowed formats
    - recursive search, case-sensitive
    - duplicates → choose first (alphabetical) + warning
  - Maintain warnings for duplicate collisions

  **Must NOT do**:
  - Do not apply fuzzy matching
  - Do not ignore case or auto-correct paths

  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
    - Reason: path/FS logic + tests
  - **Skills**: `[]`
  - **Skills Evaluated but Omitted**:
    - `playwright`: no UI

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (Tasks 1–5)
  - **Blocks**: Tasks 9–15
  - **Blocked By**: Task 1

  **References**:
  - External References: https://www.fmod.com/docs/2.02/studio/managing-assets.html (supported audio formats)

  **Acceptance Criteria**:
  - [ ] Extensionless filename resolves to a supported audio file
  - [ ] Duplicate filename returns first match + warning recorded

  **QA Scenarios**:
  ```
  Scenario: Extensionless resolution
    Tool: Bash
    Steps:
      1. Run: python -m pytest tests/test_audio_resolver.py -k extensionless
    Expected Result: Tests pass; resolver returns absolute path
    Evidence: .sisyphus/evidence/task-3-audio-extensionless.txt

  Scenario: Duplicate resolution warning
    Tool: Bash
    Steps:
      1. Run: python -m pytest tests/test_audio_resolver.py -k duplicates
    Expected Result: Tests pass; warning captured
    Evidence: .sisyphus/evidence/task-3-audio-duplicates.txt
  ```

- [x] 4. Path normalization + CSV row mapping (TDD)

  **What to do**:
  - Normalize `event_path` / `bus_path` / `bank_name` using FMOD path rules
  - Support inputs with or without `event:/` prefix by normalizing to `event:/...`
  - Validate disallowed characters and empty required fields
  - Map each row to a normalized `ImportRow` structure

  **Must NOT do**:
  - Do not accept arbitrary path prefixes
  - Do not auto-create folders or banks

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: deterministic normalization + tests
  - **Skills**: `[]`
  - **Skills Evaluated but Omitted**:
    - `playwright`: no UI

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (Tasks 1–5)
  - **Blocks**: Tasks 8–15
  - **Blocked By**: Task 2

  **References**:
  - External References: https://www.fmod.com/docs/2.02/studio/scripting-api-reference-project.html#projectlookup (path format `type:/path`)

  **Acceptance Criteria**:
  - [ ] pytest: `event_path` normalized to `event:/...`
  - [ ] pytest: invalid prefix → validation error

  **QA Scenarios**:
  ```
  Scenario: Event path normalization
    Tool: Bash
    Steps:
      1. Run: python -m pytest tests/test_path_normalization.py -k event
    Expected Result: Tests pass; event_path normalized to `event:/...`
    Evidence: .sisyphus/evidence/task-4-event-path.txt

  Scenario: Invalid prefix rejected
    Tool: Bash
    Steps:
      1. Run: python -m pytest tests/test_path_normalization.py -k invalid
    Expected Result: Tests pass; invalid path raises validation error
    Evidence: .sisyphus/evidence/task-4-invalid-prefix.txt
  ```

- [x] 5. Markdown log builder + summary stats (TDD)

  **What to do**:
  - Define Markdown log structure: header, per-row results, warnings, summary totals
  - Ensure output path is **CSV directory** with timestamped filename (avoid overwrite)
  - Provide log writer utility used by orchestrator

  **Must NOT do**:
  - Do not output elsewhere than CSV directory
  - Do not omit row-level error details

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: formatting + tests
  - **Skills**: `[]`
  - **Skills Evaluated but Omitted**:
    - `playwright`: no UI

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (Tasks 1–5)
  - **Blocks**: Tasks 11–15
  - **Blocked By**: Task 1

  **References**:
  - Pattern References: prior plans' log requirements (voiceover plan)

  **Acceptance Criteria**:
  - [ ] pytest: log file written to CSV directory
  - [ ] pytest: summary contains counts for success/fail/skip

  **QA Scenarios**:
  ```
  Scenario: Log file written to CSV directory
    Tool: Bash
    Steps:
      1. Run: python -m pytest tests/test_log_writer.py -k path
    Expected Result: Tests pass; log path equals CSV directory
    Evidence: .sisyphus/evidence/task-5-log-path.txt

  Scenario: Summary counts present
    Tool: Bash
    Steps:
      1. Run: python -m pytest tests/test_log_writer.py -k summary
    Expected Result: Tests pass; markdown includes totals
    Evidence: .sisyphus/evidence/task-5-log-summary.txt
  ```

- [x] 6. FMOD TCP client + verify probe script

  **What to do**:
  - Implement TCP client for FMOD Scripting server (port 3663)
  - Add `debug/verify_fmod_tcp.py` to execute JS and return JSON status
  - Strict error handling: connection failure → non‑zero exit

  **Must NOT do**:
  - Do not send non‑UTF8 data
  - Do not mutate project state in probe

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: network I/O + protocol correctness
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (Tasks 6–10)
  - **Blocks**: Tasks 7–15
  - **Blocked By**: Task 1

  **References**:
  - External References: https://www.fmod.com/docs/2.02/studio/scripting-terminal-reference.html (TCP scripting server)

  **Acceptance Criteria**:
  - [ ] `python debug/verify_fmod_tcp.py` returns JSON with `connected` and `exec_ok`
  - [ ] When FMOD not running, exit code is non‑zero and JSON includes error

  **QA Scenarios**:
  ```
  Scenario: Connection failure handled
    Tool: Bash
    Steps:
      1. Run: python debug/verify_fmod_tcp.py --host 127.0.0.1 --port 3664
    Expected Result: Exit code != 0; JSON includes error message
    Evidence: .sisyphus/evidence/task-6-probe-fail.txt

  Scenario: Connection success (FMOD running)
    Tool: Bash
    Preconditions: FMOD Studio running with scripting server enabled
    Steps:
      1. Run: python debug/verify_fmod_tcp.py
    Expected Result: Exit code 0; JSON shows connected=true, exec_ok=true
    Evidence: .sisyphus/evidence/task-6-probe-success.txt
  ```

- [x] 7. ManagedObject discovery + relationship map output

  **What to do**:
  - Implement discovery script to introspect ManagedObject properties/relationships
  - Emit JSON map for Event / Track / Sound / Bus / Bank objects
  - Use `ManagedObject.dump` + `relationships` per official docs

  **Must NOT do**:
  - Do not hardcode relationship names without discovery

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: scripting + introspection parsing
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (Tasks 6–10)
  - **Blocks**: Tasks 8–11
  - **Blocked By**: Task 6

  **References**:
  - External References: https://www.fmod.com/docs/2.02/studio/scripting-api-reference-project-managedobject.html

  **Acceptance Criteria**:
  - [ ] Discovery script outputs JSON with `properties` and `relationships` keys
  - [ ] Output is saved to `.sisyphus/evidence/managedobject-map.json`

  **QA Scenarios**:
  ```
  Scenario: Discovery JSON emitted
    Tool: Bash
    Preconditions: FMOD Studio running with scripting server enabled
    Steps:
      1. Run: python debug/discover_fmod_model.py
    Expected Result: JSON file exists with properties + relationships
    Evidence: .sisyphus/evidence/task-7-discovery.json

  Scenario: Missing FMOD handled
    Tool: Bash
    Steps:
      1. Run: python debug/discover_fmod_model.py --port 3664
    Expected Result: Exit code != 0; error logged
    Evidence: .sisyphus/evidence/task-7-discovery-fail.txt
  ```

- [x] 8. Create‑only JS builder (event/track/sound)

  **What to do**:
  - Build JS script generator that:
    - Creates event via `studio.project.create('Event')`
    - Adds group track `event.addGroupTrack(name)`
    - Adds sound via `groupTrack.addSound(parameter, soundType, start, length)`
    - Attaches imported audio asset to sound (per Asset API)
  - Ensure JS returns structured JSON result per row

  **Must NOT do**:
  - Do not use template cloning or undocumented APIs

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: scripting correctness + JSON bridging
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (Tasks 6–10)
  - **Blocks**: Tasks 11–15
  - **Blocked By**: Task 6, Task 7

  **References**:
  - https://www.fmod.com/docs/2.02/studio/scripting-api-reference-project.html#projectcreate
  - https://www.fmod.com/docs/2.02/studio/scripting-api-reference-project-model-event.html#eventaddgrouptrack
  - https://www.fmod.com/docs/2.02/studio/scripting-api-reference-project-model-track.html#grouptrackaddsound
  - https://www.fmod.com/docs/2.02/studio/scripting-api-reference-project-model-sound.html#modelsinglesound

  **Acceptance Criteria**:
  - [ ] JS builder returns valid JSON schema for success/failure
  - [ ] Generated JS avoids undocumented calls

  **QA Scenarios**:
  ```
  Scenario: JS builder produces valid JSON
    Tool: Bash
    Steps:
      1. Run: python -m pytest tests/test_js_builder.py -k json
    Expected Result: Tests pass; JSON schema valid
    Evidence: .sisyphus/evidence/task-8-js-json.txt

  Scenario: API usage verified
    Tool: Bash
    Steps:
      1. Run: python -m pytest tests/test_js_builder.py -k api
    Expected Result: Tests pass; only whitelisted API symbols used
    Evidence: .sisyphus/evidence/task-8-js-api.txt
  ```

- [x] 9. Audio import + asset folder routing

  **What to do**:
  - Use `studio.project.importAudioFile(filePath)` (absolute path)
  - Reassign imported asset to target asset path via folder relationships
  - Return asset GUID/path for later linkage

  **Must NOT do**:
  - Do not import using relative paths
  - Do not write outside audio bin hierarchy

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: FMOD scripting correctness
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (Tasks 6–10)
  - **Blocks**: Tasks 11–15
  - **Blocked By**: Task 6, Task 7

  **References**:
  - https://www.fmod.com/docs/2.02/studio/scripting-api-reference-project.html#projectimportaudiofile
  - https://www.fmod.com/docs/2.02/studio/scripting-api-reference-project-model-folder.html#masterassetfoldergetasset

  **Acceptance Criteria**:
  - [ ] Imported asset is placed in target asset folder
  - [ ] Null return on import failure triggers row error

  **QA Scenarios**:
  ```
  Scenario: Import succeeds
    Tool: Bash
    Preconditions: FMOD Studio running; audio file exists
    Steps:
      1. Run: python debug/run_import_single.py --audio <path>
    Expected Result: JSON indicates asset GUID/path
    Evidence: .sisyphus/evidence/task-9-import-success.txt

  Scenario: Import fails for missing file
    Tool: Bash
    Steps:
      1. Run: python debug/run_import_single.py --audio <missing>
    Expected Result: JSON error; row marked failed
    Evidence: .sisyphus/evidence/task-9-import-fail.txt
  ```

- [x] 10. Bus/Bank lookup + relationship assignment

  **What to do**:
  - Lookup bus/bank via `project.lookup('bus:/...')` and `project.lookup('bank:/...')`
  - Attach bus/bank relationships using `ManagedObject.relationships.<name>.add`
  - If lookup fails, **log warning and mark row as skipped** (no event created)

  **Must NOT do**:
  - Do not create new buses or banks

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: relationship API correctness
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (Tasks 6–10)
  - **Blocks**: Tasks 11–15
  - **Blocked By**: Task 7

  **References**:
  - https://www.fmod.com/docs/2.02/studio/scripting-api-reference-project.html#projectlookup
  - https://www.fmod.com/docs/2.02/studio/scripting-api-reference-project-managedobject.html#managedrelationshipadd
  - User screenshot: Project.Model.Bank (Bank.getPath)
  - User screenshot: Project.Model.MixerStrip (MixerStrip.getPath)

  **Acceptance Criteria**:
  - [ ] Valid bus/bank paths attach successfully
  - [ ] Missing bus/bank produces warning; row is skipped (no event created)

  **QA Scenarios**:
  ```
  Scenario: Valid bus/bank attach
    Tool: Bash
    Preconditions: FMOD project contains bus/bank
    Steps:
      1. Run: python debug/run_attach_bus_bank.py --bus bus:/sfx --bank bank:/SFX
    Expected Result: JSON indicates relationships attached
    Evidence: .sisyphus/evidence/task-10-attach-ok.txt

  Scenario: Missing bus/bank warning
    Tool: Bash
    Steps:
      1. Run: python debug/run_attach_bus_bank.py --bus bus:/missing --bank bank:/missing
    Expected Result: JSON warning; row marked skipped
    Evidence: .sisyphus/evidence/task-10-attach-missing.txt
  ```

- [x] 11. Orchestrator: row‑by‑row execution + error handling

  **What to do**:
  - Orchestrate the full CSV flow: resolve audio → **pre-check bus/bank** → import asset → create event → bind sound → attach bus/bank → log result
  - Fail row-by-row; never stop entire batch unless TCP connection fails
  - Capture structured per-row status (success/skip/fail)
  - **If event_path already exists**: skip row and log warning (do not modify existing event)

  **Must NOT do**:
  - Do not silently ignore errors
  - Do not skip logging for any row

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: multi-step control flow + failure isolation
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3 (Tasks 11–15)
  - **Blocks**: Task 15
  - **Blocked By**: Tasks 2–10

  **References**:
  - Prior plans: `plans/fmod-import-main-flow-fix.md`, `plans/fmod-batch-import-voiceover.md`
  - Official docs for each API used in steps

  **Acceptance Criteria**:
  - [ ] One failing row does not stop subsequent rows
  - [ ] Log includes per-row status + error message

  **QA Scenarios**:
  ```
  Scenario: Row failure does not stop batch
    Tool: Bash
    Steps:
      1. Run: python debug/run_batch.py --csv fixtures/mixed.csv
    Expected Result: Success rows processed after a failing row
    Evidence: .sisyphus/evidence/task-11-row-continue.txt

  Scenario: TCP failure stops batch
    Tool: Bash
    Steps:
      1. Run: python debug/run_batch.py --csv fixtures/sample.csv --port 3664
    Expected Result: Batch aborts with connection error
    Evidence: .sisyphus/evidence/task-11-tcp-fail.txt
  ```

- [x] 12. GUI dialog flow + FMOD launch/reconnect

  **What to do**:
  - Provide GUI dialogs to select CSV, audio directory, and optional FMOD project
  - If FMOD not running, prompt user to start (or open project) and retry

  **Must NOT do**:
  - Do not require CLI inputs

  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
    - Reason: Tkinter dialogs + simple control flow
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (Tasks 11–15)
  - **Blocks**: Task 13
  - **Blocked By**: Task 1

  **References**:
  - Python tkinter file dialogs

  **Acceptance Criteria**:
  - [ ] Double-click launch presents CSV/audio selections
  - [ ] Canceling any dialog exits cleanly

  **QA Scenarios**:
  ```
  Scenario: Dialog selection flow (test mode)
    Tool: Bash
    Steps:
      1. Run: set FMOD_IMPORTER_TEST_MODE=1 && python -m fmod_batch_import
    Expected Result: Test mode uses fixture paths and proceeds to import
    Evidence: .sisyphus/evidence/task-12-dialog-flow.txt

  Scenario: Cancel exits cleanly (test mode)
    Tool: Bash
    Steps:
      1. Run: set FMOD_IMPORTER_TEST_MODE=cancel && python -m fmod_batch_import
    Expected Result: Program exits without error
    Evidence: .sisyphus/evidence/task-12-dialog-cancel.txt
  ```

- [x] 13. .bat entrypoint (no CLI input)

  **What to do**:
  - Provide `.bat` that invokes python entry (no arguments)
  - Ensure environment path detection is simple and local only

  **Must NOT do**:
  - Do not require user to type in terminal

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: simple launcher
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (Tasks 11–15)
  - **Blocks**: Task 15
  - **Blocked By**: Task 12

  **References**:
  - Windows .bat best practices

  **Acceptance Criteria**:
  - [ ] Double-click runs without CLI arguments
  - [ ] Exit code propagated to console/log if run from shell

  **QA Scenarios**:
  ```
  Scenario: .bat launches successfully (test mode)
    Tool: Bash
    Steps:
      1. Run: cmd /c path\to\launcher.bat
    Expected Result: Test mode runs without CLI args; exit code 0
    Evidence: .sisyphus/evidence/task-13-bat-launch.txt

  Scenario: .bat run from shell
    Tool: Bash
    Steps:
      1. Run: cmd /c path\to\launcher.bat
    Expected Result: Exit code 0 on success
    Evidence: .sisyphus/evidence/task-13-bat-shell.txt
  ```

- [x] 14. Markdown report integration + export

  **What to do**:
  - Integrate log writer into orchestrator
  - Ensure Markdown includes per-row details + summary
  - Save to CSV directory with timestamped filename (avoid overwrite)

  **Must NOT do**:
  - Do not overwrite without warning if file exists

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: simple formatting
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (Tasks 11–15)
  - **Blocks**: Task 15
  - **Blocked By**: Task 11

  **References**:
  - Task 5 log builder

  **Acceptance Criteria**:
  - [ ] Log file exists in CSV directory with Markdown structure
  - [ ] Summary totals match processed rows

  **QA Scenarios**:
  ```
  Scenario: Markdown report written
    Tool: Bash
    Steps:
      1. Run: python debug/run_batch.py --csv fixtures/sample.csv
    Expected Result: Markdown log created next to CSV
    Evidence: .sisyphus/evidence/task-14-log-written.txt

  Scenario: Summary totals correct
    Tool: Bash
    Steps:
      1. Run: python -m pytest tests/test_log_summary.py
    Expected Result: Tests pass
    Evidence: .sisyphus/evidence/task-14-log-summary.txt
  ```

- [x] 15. Stepwise integration tests (end → start)

  **What to do**:
  - Implement integration test sequence:
    1) Audio import only
    2) Event creation only
    3) Event configuration update
    4) Full CSV mapping
  - Each step must pass before running the next

  **Must NOT do**:
  - Do not run full batch if earlier step fails

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: multi-step integration coordination
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3 (Tasks 11–15)
  - **Blocks**: Final verification wave
  - **Blocked By**: Tasks 6–14

  **References**:
  - Stepwise testing requirement from user

  **Acceptance Criteria**:
  - [ ] Each step produces evidence file before next executes
  - [ ] Final end-to-end test succeeds with sample CSV

  **QA Scenarios**:
  ```
  Scenario: Stepwise flow
    Tool: Bash
    Steps:
      1. Run: python debug/run_stepwise_tests.py
    Expected Result: Steps 1–4 pass sequentially; evidence files created
    Evidence: .sisyphus/evidence/task-15-stepwise.txt

  Scenario: Early failure halts
    Tool: Bash
    Steps:
      1. Run: python debug/run_stepwise_tests.py --simulate-missing-audio
    Expected Result: Flow stops after step 1; later steps not executed
    Evidence: .sisyphus/evidence/task-15-stepwise-fail.txt
  ```


---

## Final Verification Wave

- [ ] F1. **Plan Compliance Audit** — `oracle`
- [ ] F2. **Code Quality Review** — `unspecified-high`
- [ ] F3. **Real Manual QA** — `unspecified-high`
- [ ] F4. **Scope Fidelity Check** — `deep`

---

## Commit Strategy

- **1**: `feat(scaffold): init batch import package + tests`
- **2**: `feat(fmod): add TCP client + create-only import`
- **3**: `feat(ui): add GUI dialog + bat entry`

---

## Success Criteria

### Verification Commands
```bash
python -m pytest
```

### Final Checklist
- [ ] All Must Have items present
- [ ] All Must NOT Have items absent
- [ ] All tests pass
- [ ] Markdown log produced next to CSV
