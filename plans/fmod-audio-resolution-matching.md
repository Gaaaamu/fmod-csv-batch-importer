# FMOD Batch Import: Audio Resolution Matching Fix

## TL;DR

> **Quick Summary**: Fix audio resolution so CSV base names resolve correctly to FMOD-supported audio files by adding extensionless, recursive, case-sensitive matching with deterministic selection and warning/logging for duplicates. Use TDD to lock behavior with tests.
>
> **Deliverables**:
> - Updated audio discovery/resolution logic (extensionless + exact extension handling)
> - Duplicate detection warnings (console + markdown log)
> - TDD tests covering matching, recursion, case sensitivity, duplicates
>
> **Estimated Effort**: Short
> **Parallel Execution**: YES — 2 waves
> **Critical Path**: Matching rules → duplicate warnings → orchestrator integration → tests

---

## Context

### Original Request
用户反馈导入结果全被跳过，日志显示 `Audio resolution failed: not_found`。要求：CSV 的 `audio_path` 不需要扩展名，递归搜索子目录，大小写敏感，重名时选第一个匹配并给出警告与日志。支持 FMOD 2.02.07 可导入的格式。

### Interview Summary
**Key Discussions**:
- `audio_path` 不需要扩展名；若包含扩展名则按完整文件名精确匹配
- 递归搜索子目录
- 大小写敏感、仅允许纯文件名（不含子路径）
- 重名时：按路径字母序选第一个，警告只记录一次（控制台+日志）
- 支持 FMOD 官方可导入格式（.wav, .mp3, .ogg, .aif, .aiff, .wma, .flac）
- 测试策略：TDD

**Research Findings**:
- 日志：30 行全部 `Audio resolution failed: not_found`
- CSV 基础名无扩展名
- 音频目录存在对应 .wav 文件
- FMOD 2.02 可导入格式来自官方文档（https://www.fmod.com/docs/2.02/studio/managing-assets.html#compatible-file-formats）

### Metis Review
**Identified Gaps (addressed)**:
- 当前发现逻辑要求带扩展名，重名视为错误 → 将改为允许无扩展名 + 重名警告
- 需测试覆盖递归/大小写/重名策略 → TDD 方案覆盖

---

## Work Objectives

### Core Objective
修复音频解析失败问题：允许 CSV 使用无扩展名的基础文件名，递归查找 FMOD 支持格式，大小写敏感，重名时按路径排序选择并记录警告。

### Concrete Deliverables
- 音频解析逻辑更新（extensionless + exact extension match）
- 重名检测与警告输出（console + markdown log）
- TDD 测试覆盖关键规则

### Definition of Done
- [x] CSV 基础名可正确解析到音频文件（按 FMOD 支持格式）
- [x] 递归搜索生效，大小写敏感
- [x] 重名时选择字母序第一个并输出一次警告（console + log）
- [x] `pytest -q` 全部通过

### Must Have
- 仅允许 base filename（拒绝带路径分隔符的 audio_path）
- 若 CSV 包含扩展名 → 精确匹配该文件名
- 重名时不报错终止，改为警告 + 选第一个
- 支持 FMOD 2.02 可导入格式

### Must NOT Have (Guardrails)
- 不增加模糊匹配/后缀猜测（如 `_2`）
- 不改变 CSV schema
- 不新增依赖

---

## Verification Strategy (MANDATORY)

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed.

### Test Decision
- **Automated tests**: TDD
- **Framework**: pytest

### QA Policy
每个任务包含 agent-executed QA 场景。证据保存至 `.sisyphus/evidence/`。

---

## Execution Strategy

### Parallel Execution Waves

Wave 1 (Rules + Tests)
├── Task 1: 扩展名/基础名匹配规则更新（TDD）
├── Task 2: 递归搜索与大小写敏感规则（TDD）
└── Task 3: 重名检测 + 警告输出（TDD）

Wave 2 (Integration)
├── Task 4: Orchestrator 集成与日志联动（TDD）
└── Task 5: 端到端回归测试 + 样例验证

Critical Path: 1 → 2 → 3 → 4 → 5

### Dependency Matrix
- **1**: — → 4,5
- **2**: — → 4,5
- **3**: — → 4,5
- **4**: 1,2,3 → 5
- **5**: 4 → —

### Agent Dispatch Summary
- Wave 1: Task 1-3 → `unspecified-high`
- Wave 2: Task 4-5 → `unspecified-high`

---

## TODOs

- [x] 1. 扩展名/基础名匹配规则更新（TDD）

  **What to do**:
  - 更新 `audio_discovery` 中解析逻辑：
    - CSV 若带扩展名 → 精确匹配文件名
    - CSV 不带扩展名 → 搜索 FMOD 支持扩展名列表
  - 拒绝 `audio_path` 含路径分隔符
  - 新增单元测试覆盖上述规则

  **Must NOT do**:
  - 不添加后缀猜测（如 `_2`）
  - 不改 CSV schema

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: 规则细节 + 测试覆盖
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 2,3)
  - **Blocks**: 4,5
  - **Blocked By**: None

  **References**:
  - `src/fmod_batch_import/audio_discovery.py` — 当前解析逻辑
  - `tests/test_audio_discovery.py` — 测试结构与模式
  - FMOD 格式列表: https://www.fmod.com/docs/2.02/studio/managing-assets.html#compatible-file-formats

  **Acceptance Criteria**:
  - [x] `pytest -q tests/test_audio_discovery.py::test_extensionless_resolves_supported_formats` → PASS
  - [x] `pytest -q tests/test_audio_discovery.py::test_extension_specified_requires_exact_filename` → PASS
  - [x] `pytest -q tests/test_audio_discovery.py::test_audio_path_rejects_subpaths` → PASS

  **QA Scenarios**:
  ```
  Scenario: extensionless name resolves supported format
    Tool: Bash
    Steps:
      1. pytest -q tests/test_audio_discovery.py::test_extensionless_resolves_supported_formats
    Expected Result: tests pass
    Evidence: .sisyphus/evidence/task-1-extensionless.txt

  Scenario: extension specified requires exact match
    Tool: Bash
    Steps:
      1. pytest -q tests/test_audio_discovery.py::test_extension_specified_requires_exact_filename
    Expected Result: tests pass
    Evidence: .sisyphus/evidence/task-1-exact-ext.txt
  ```

- [x] 2. 递归搜索与大小写敏感规则（TDD）

  **What to do**:
  - 确保递归搜索覆盖子目录
  - 明确大小写敏感匹配（case-sensitive）
  - 测试覆盖递归与大小写行为

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: 4,5
  - **Blocked By**: None

  **References**:
  - `src/fmod_batch_import/audio_discovery.py`
  - `tests/test_audio_discovery.py`

  **Acceptance Criteria**:
  - [x] `pytest -q tests/test_audio_discovery.py::test_recursive_search_finds_subdir_files` → PASS
  - [x] `pytest -q tests/test_audio_discovery.py::test_case_sensitive_matching` → PASS

  **QA Scenarios**:
  ```
  Scenario: recursive search resolves nested file
    Tool: Bash
    Steps:
      1. pytest -q tests/test_audio_discovery.py::test_recursive_search_finds_subdir_files
    Expected Result: tests pass
    Evidence: .sisyphus/evidence/task-2-recursive.txt

  Scenario: case-sensitive mismatch is rejected
    Tool: Bash
    Steps:
      1. pytest -q tests/test_audio_discovery.py::test_case_sensitive_matching
    Expected Result: tests pass
    Evidence: .sisyphus/evidence/task-2-case.txt
  ```

- [x] 3. 重名检测 + 警告输出（TDD）

  **What to do**:
  - 当一个 base name 匹配多个文件时：
    - 按路径字母序排序
    - 选第一个作为结果
    - 发出一次 warning（console + log），包含：冲突数量 + 选中路径
  - 测试重名行为 + 警告输出

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: 4,5
  - **Blocked By**: None

  **References**:
  - `src/fmod_batch_import/audio_discovery.py`
  - `src/fmod_batch_import/logger.py` — 现有日志风格
  - `tests/test_logger.py` — 日志测试模式

  **Acceptance Criteria**:
  - [x] `pytest -q tests/test_audio_discovery.py::test_duplicate_selects_first_and_warns` → PASS
  - [x] `pytest -q tests/test_logger.py::test_duplicate_warning_logged` → PASS

  **QA Scenarios**:
  ```
  Scenario: duplicate chooses first + warning
    Tool: Bash
    Steps:
      1. pytest -q tests/test_audio_discovery.py::test_duplicate_selects_first_and_warns
    Expected Result: tests pass
    Evidence: .sisyphus/evidence/task-3-duplicate.txt
  ```

- [x] 4. Orchestrator 集成与日志联动（TDD）

  **What to do**:
  - 确保解析结果与 orchestrator 流程一致
  - 确保 warning 同时落日志与 console
  - 增加针对 orchestrator 的测试覆盖

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2
  - **Blocks**: 5
  - **Blocked By**: 1,2,3

  **References**:
  - `src/fmod_batch_import/orchestrator.py`
  - `tests/test_orchestrator.py`

  **Acceptance Criteria**:
  - [x] `pytest -q tests/test_orchestrator.py::test_audio_resolution_warning_logged` → PASS

  **QA Scenarios**:
  ```
  Scenario: orchestrator logs warning on duplicate
    Tool: Bash
    Steps:
      1. pytest -q tests/test_orchestrator.py::test_audio_resolution_warning_logged
    Expected Result: tests pass
    Evidence: .sisyphus/evidence/task-4-orchestrator.txt
  ```

- [x] 5. 端到端回归测试 + 样例验证

  **What to do**:
  - 使用样例 CSV + 音频目录 fixture 进行回归验证
  - 验证日志输出与统计正确

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2
  - **Blocks**: —
  - **Blocked By**: 4

  **References**:
  - `tests/test_integration.py`

  **Acceptance Criteria**:
  - [x] `pytest -q tests/test_integration.py::test_extensionless_audio_resolution` → PASS

  **QA Scenarios**:
  ```
  Scenario: end-to-end resolution succeeds
    Tool: Bash
    Steps:
      1. pytest -q tests/test_integration.py::test_extensionless_audio_resolution
    Expected Result: tests pass
    Evidence: .sisyphus/evidence/task-5-e2e.txt
  ```

---

## Final Verification Wave

- [x] F1. **Plan Compliance Audit** — `oracle`
- [x] F2. **Code Quality Review** — `unspecified-high`
- [x] F3. **Runtime QA (mocked)** — `unspecified-high`
- [x] F4. **Scope Fidelity Check** — `deep`

---

## Commit Strategy

- **1**: `fix(audio): resolve extensionless matches + duplicate warnings`
- **2**: `test(audio): add resolution and warning coverage`

---

## Success Criteria

### Verification Commands
```bash
pytest -q
```

### Final Checklist
- [x] CSV 基础名可解析到音频文件
- [x] 递归搜索 + 大小写敏感生效
- [x] 重名警告出现在 log + console
- [x] 所有测试通过
