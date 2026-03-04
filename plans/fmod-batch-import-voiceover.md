# FMOD 批量旁白导入与模板 Event 套用方案

## TL;DR

> **Quick Summary**: 构建一个可双击运行的 Python 工具，通过 TCP 连接到已打开的 FMOD Studio 项目，读取 CSV 与音频目录，克隆示例 event 并导入/绑定音频，按规则覆盖 bus/bank 与路径层级，输出 Markdown 日志。
>
> **Deliverables**:
> - 可双击运行的批量导入工具（Python）
> - CSV 规范与示例
> - 完整的 Markdown 日志与错误摘要
>
> **Estimated Effort**: Medium
> **Parallel Execution**: YES — 3 waves
> **Critical Path**: CSV 解析规则 → FMOD TCP 客户端 → 模板克隆/音频绑定 → 端到端编排

---

## Context

### Original Request
用户希望批量导入旁白音频到 FMOD audio assets，并根据一个已配置的示例 event 套用音量/ADSR/淡入淡出/轨道等编辑信息，同时可通过 CSV 指定 event/asset 目录层级与 bus/bank。要求操作简洁（双击脚本、弹窗选择 CSV 与音频目录），FMOD 版本 2.02.07。

### Interview Summary
**Key Discussions**:
- 采用外部脚本（Python）+ 双击运行；弹窗选择 CSV、音频目录、示例 event；FMOD 已打开，通过 TCP (3663) 通信。
- CSV 单文件字段：`audio_path`, `event_path`, `asset_path`, `bus_path`, `bank_name`（使用 FMOD 前缀）。
- `event_path` 即 event 路径与名称（不再区分 event_name）。
- `audio_path` 仅文件名；递归搜索音频目录；同名冲突报错跳过。
- asset_path 为空时不继承上一条；默认按音频目录结构映射；CSV 明确给值则覆盖。
- 冲突策略：event/asset 已存在则自动重命名（_001）并记录。
- bus/bank：CSV 允许覆盖；若 CSV 为空且示例 event 也无 → master bus / 不分配 bank。
- 仅旁白使用，混音简单；支持 FMOD 可导入的音频格式，其他跳过并记录日志。
- 日志输出为 Markdown，放在 CSV 同目录。
- 测试策略：TDD，pytest。

**Research Findings**:
- FMOD Studio 2.02 提供 JS Scripting API，可通过 TCP (3663) 发送脚本执行；支持 `importAudioFile`, `copy()`, `assignToBank`, `mixerGroup` 等关键操作。
- 无 headless 模式；GUI 需初始化；导入音频建议使用绝对路径。

### Metis Review
**Identified Gaps (addressed)**:
- CSV 编码/分隔符与错误策略需明确 → 在本计划中设定默认值并体现在验证与日志中。
- 模板 event 复杂度与 API 可用性风险 → 增加模板验证与失败日志策略。
- 冲突与异常处理需有明确验收标准 → 在任务验收中加入日志与计数校验。

---

## Work Objectives

### Core Objective
实现一个稳定、可双击运行的批量导入工具，基于 CSV 与音频目录自动创建/克隆 event、导入音频、设置 bus/bank，输出可追溯的 Markdown 日志，并提供完整测试。

### Concrete Deliverables
- Python 批量导入工具（含 UI 选择 CSV/音频目录/模板 event）
- CSV 规范说明与样例文件
- 日志输出（Markdown）与汇总统计
- pytest 测试覆盖核心逻辑（TDD）

### Definition of Done
- [x] `pytest -q` 全部通过
- [x] 工具可在 FMOD 已打开项目中完成批量导入，生成 event 与 asset 并记录日志
- [x] 所有异常路径（重复、缺失、格式不支持）均记录日志且不中断整体执行
- [x] CSV 日志包含汇总统计（成功/跳过/失败计数）与每行处理结果

### Must Have
- CSV 驱动 event/asset/bus/bank 组织与覆盖逻辑
- 使用示例 event 克隆，继承其音频编辑与轨道配置
- FMOD 2.02.07 兼容 + TCP 驱动方式
- 可双击运行 + 弹窗选择
- CSV 解析规则：UTF-8（可含 BOM）、首行为 header、逗号分隔、空字段允许
- 错误策略：逐行处理，错误行记录日志并跳过，不终止整体执行（除非 FMOD 连接失败）
- 不自动创建 bus/bank，仅使用已存在对象

### Must NOT Have (Guardrails)
- 不引入复杂混音处理或多轨自动编排
- 不自动创建/猜测未知 bus/bank
- 不在无明确需求时增加复杂 UI 或数据库

---

## Verification Strategy (MANDATORY)

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed.

### Test Decision
- **Infrastructure exists**: NO (greenfield)
- **Automated tests**: TDD
- **Framework**: pytest

### QA Policy
每个任务包含 agent-executed QA 场景（命令/断言/证据文件）。
证据保存至 `.sisyphus/evidence/`。

---

## Execution Strategy

### Parallel Execution Waves

Wave 1 (Foundation — can start immediately)
├── Task 1: 项目脚手架与运行入口（Python）
├── Task 2: CSV 规范与解析 + 默认/继承规则（TDD）
├── Task 3: 音频发现/冲突检测与 asset 路径映射（TDD）
├── Task 4: FMOD 路径规范化与默认回退规则（TDD）
└── Task 5: Markdown 日志与统计输出模块（TDD）

Wave 2 (Core FMOD Integration)
├── Task 6: FMOD TCP 客户端抽象 + 连接健康检查（TDD）
├── Task 7: 模板 event 验证 + 克隆与命名冲突处理（TDD）
├── Task 8: 音频导入 + 绑定到模板轨道（TDD）
├── Task 9: bus/bank 覆盖逻辑 + 默认回退（TDD）
└── Task 10: 导入编排器（CSV → FMOD 操作 → 日志）

Wave 3 (UX + E2E)
├── Task 11: 弹窗选择 CSV/音频目录/模板 event + 启动流程
└── Task 12: 端到端集成测试与示例数据

Critical Path: 2 → 6 → 7 → 8 → 10 → 12
Parallel Speedup: ~60% vs sequential

### Dependency Matrix

- **1**: — → 2,3,4,5,11
- **2**: 1 → 10,12
- **3**: 1 → 10,12
- **4**: 1 → 7,8,9,10
- **5**: 1 → 10,12
- **6**: 1 → 7,8,9,10,11
- **7**: 4,6 → 8,9,10
- **8**: 4,6,7 → 10,12
- **9**: 4,6,7 → 10,12
- **10**: 2,3,5,6,7,8,9 → 12
- **11**: 1,6 → 12
- **12**: 2,3,5,6,7,8,9,10,11 → —

### Agent Dispatch Summary
- **Wave 1**: T1 quick, T2/T3/T4 unspecified-high, T5 quick
- **Wave 2**: T6/T7/T8/T9/T10 unspecified-high
- **Wave 3**: T11 quick, T12 unspecified-high

---

## TODOs

- [x] 1. 初始化 Python 项目脚手架与双击入口

  **What to do**:
  - 创建最小可运行的 Python 项目结构（src/, tests/, README）
  - 提供双击入口（如 `run.bat` 或打包入口）仅调用主模块
  - 确保 Windows 中文路径与空格路径可运行

  **Must NOT do**:
  - 不添加复杂 GUI（仅使用文件选择对话框）

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: 轻量脚手架与入口脚本
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 2-5)
  - **Blocks**: 2,3,4,5,11
  - **Blocked By**: None

  **References**:
  - N/A (greenfield)

  **Acceptance Criteria**:
  - [x] 项目结构存在且 `python -m <module>` 可启动（空实现允许）

  **QA Scenarios**:
  ```
  Scenario: 启动入口不报错
    Tool: Bash
    Steps:
      1. 运行 `python -m <module>`
    Expected Result: 进程退出码 0 或进入等待状态
    Evidence: .sisyphus/evidence/task-1-launch.txt
  ```

- [x] 2. CSV 解析与默认规则（TDD）

  **What to do**:
  - 实现 CSV 解析（UTF-8/BOM/逗号/带 header）
  - 解析字段：audio_path, event_path, asset_path, bus_path, bank_name
  - 规则：空字段回退到示例 event；event_path 为空时默认 `event:/event_<filename>`
  - 记录行级解析错误但不中断整体

  **Must NOT do**:
  - 不引入新增 CSV 字段

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: 规则多、边界多，需要严谨测试
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1,3,4,5)
  - **Blocks**: 10,12
  - **Blocked By**: 1

  **References**:
  - CSV 规则（本计划 Must Have）

  **Acceptance Criteria**:
  - [x] pytest: CSV header/编码/空字段回退通过

  **QA Scenarios**:
  ```
  Scenario: CSV 空字段回退规则正确
    Tool: Bash
    Steps:
      1. 运行 `pytest -q tests/test_csv_rules.py`
    Expected Result: tests pass
    Evidence: .sisyphus/evidence/task-2-pytest.txt
  ```

- [x] 3. 音频发现与 asset 路径映射（TDD）

  **What to do**:
  - audio_path 仅文件名 → 递归遍历音频目录匹配
  - 同名冲突：报错并跳过（记录日志）
  - asset_path 为空时：按音频目录结构映射到 assets（顶层=所选音频目录）
  - 若 CSV 给 asset_path，则覆盖默认映射

  **Must NOT do**:
  - 不自动修正同名冲突

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: 规则多且涉及文件系统边界
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1,2,4,5)
  - **Blocks**: 10,12
  - **Blocked By**: 1

  **Acceptance Criteria**:
  - [x] pytest: 冲突检测与映射逻辑全通过

  **QA Scenarios**:
  ```
  Scenario: 同名音频冲突被记录并跳过
    Tool: Bash
    Steps:
      1. 运行 `pytest -q tests/test_audio_discovery.py::test_duplicate_filename`
    Expected Result: tests pass
    Evidence: .sisyphus/evidence/task-3-duplicate.txt
  ```

- [x] 4. FMOD 路径规范化与默认回退（TDD）

  **What to do**:
  - 校验/规范化 event_path、asset_path、bus_path、bank_name 前缀
  - 若 CSV 与示例 event 都空：bus → master，bank → 无分配

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: 7,8,9,10
  - **Blocked By**: 1

  **Acceptance Criteria**:
  - [x] pytest: 路径规范化与回退逻辑通过

  **QA Scenarios**:
  ```
  Scenario: bus/bank 回退到 master / none
    Tool: Bash
    Steps:
      1. 运行 `pytest -q tests/test_path_defaults.py`
    Expected Result: tests pass
    Evidence: .sisyphus/evidence/task-4-defaults.txt
  ```

- [x] 5. Markdown 日志与统计输出模块（TDD）

  **What to do**:
  - 生成 Markdown 日志（CSV 同目录）
  - 记录每行处理结果（成功/跳过/失败）
  - 输出汇总统计（成功/跳过/失败计数）

  **Must NOT do**:
  - 不写入除 CSV 目录外的日志

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: 结构化输出与计数逻辑
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: 10,12
  - **Blocked By**: 1

  **Acceptance Criteria**:
  - [x] pytest: 日志结构与汇总计数校验通过

  **QA Scenarios**:
  ```
  Scenario: 生成 Markdown 日志
    Tool: Bash
    Steps:
      1. 运行 `pytest -q tests/test_logging.py`
    Expected Result: tests pass
    Evidence: .sisyphus/evidence/task-5-logging.txt
  ```

- [x] 6. FMOD TCP 客户端抽象 + 连接健康检查（TDD）

  **What to do**:
  - 建立 TCP 连接（localhost:3663）与超时处理
  - 支持发送 JS 片段并读取响应
  - 连接失败时返回明确错误并记录日志

  **Must NOT do**:
  - 不自动启动 FMOD

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: 网络通信与错误处理
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: 7,8,9,10,11
  - **Blocked By**: 1

  **References**:
  - FMOD Scripting Terminal Reference: https://www.fmod.com/docs/2.02/studio/scripting-terminal-reference.html

  **Acceptance Criteria**:
  - [x] pytest: TCP 客户端连接/超时/错误处理用例通过

  **QA Scenarios**:
  ```
  Scenario: TCP 连接失败时有清晰错误
    Tool: Bash
    Steps:
      1. 确保未开启任何 3663 端口服务
      2. 运行 `pytest -q tests/test_fmod_tcp.py::test_connection_failure`
    Expected Result: tests pass
    Evidence: .sisyphus/evidence/task-6-tcp-fail.txt
  ```

- [x] 7. 模板 event 验证 + 克隆与命名冲突处理（TDD）

  **What to do**:
  - 校验模板 event 存在且为“单轨 + 单音频”结构
  - 克隆模板 event，并按 event_path 设置目录/名称
  - event 冲突时自动重命名（_001 等）并记录

  **Must NOT do**:
  - 不在模板结构不符合时继续导入

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: FMOD 对象模型与冲突处理
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: 8,9,10
  - **Blocked By**: 4,6

  **References**:
  - FMOD Scripting API (Project): https://www.fmod.com/docs/2.02/studio/scripting-api-reference-project.html

  **Acceptance Criteria**:
  - [x] pytest: 模板结构验证与重命名逻辑通过

  **QA Scenarios**:
  ```
  Scenario: 模板 event 结构不符时中止
    Tool: Bash
    Steps:
      1. 运行 `pytest -q tests/test_template_validation.py::test_invalid_template`
    Expected Result: tests pass
    Evidence: .sisyphus/evidence/task-7-template-invalid.txt
  ```

- [x] 8. 音频导入 + 绑定到模板轨道（TDD）

  **What to do**:
  - 使用绝对路径导入音频 asset
  - 替换模板事件中单一音频引用为新导入 asset
  - 若模板未找到单一音频引用，记录错误并跳过该行

  **Must NOT do**:
  - 不改变模板的其他编辑属性（淡入淡出/ADSR 等保留）

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: FMOD 音频绑定细节与对象操作
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: 10,12
  - **Blocked By**: 4,6,7

  **References**:
  - FMOD Scripting API (Project): https://www.fmod.com/docs/2.02/studio/scripting-api-reference-project.html

  **Acceptance Criteria**:
  - [x] pytest: 导入调用使用绝对路径且绑定成功（mock）

  **QA Scenarios**:
  ```
  Scenario: 导入与绑定接口调用正确
    Tool: Bash
    Steps:
      1. 运行 `pytest -q tests/test_audio_binding.py`
    Expected Result: tests pass
    Evidence: .sisyphus/evidence/task-8-audio-bind.txt
  ```

- [x] 9. bus/bank 覆盖逻辑 + 默认回退（TDD）

  **What to do**:
  - CSV 给出 bus_path/bank_name → 覆盖模板值
  - CSV 空且模板也空 → bus=master, bank=none
  - 不存在的 bus/bank → 记录日志并跳过该行

  **Must NOT do**:
  - 不自动创建 bus/bank

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: 规则多，需严格处理错误
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: 10,12
  - **Blocked By**: 4,6,7

  **References**:
  - FMOD Scripting API (Project): https://www.fmod.com/docs/2.02/studio/scripting-api-reference-project.html

  **Acceptance Criteria**:
  - [x] pytest: 覆盖/回退/不存在对象处理通过

  **QA Scenarios**:
  ```
  Scenario: bus/bank 不存在时跳过并记录
    Tool: Bash
    Steps:
      1. 运行 `pytest -q tests/test_bus_bank_rules.py::test_missing_bus`
    Expected Result: tests pass
    Evidence: .sisyphus/evidence/task-9-bus-bank.txt
  ```

- [x] 10. 导入编排器（CSV → FMOD 操作 → 日志）

  **What to do**:
  - 串联 CSV 解析、音频发现、模板克隆、导入绑定、bus/bank、日志
  - 逐行处理，错误行不影响后续
  - FMOD 连接失败则整体终止并记录

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2
  - **Blocks**: 12
  - **Blocked By**: 2,3,5,6,7,8,9

  **Acceptance Criteria**:
  - [x] pytest: 编排器成功与失败路径覆盖通过

  **QA Scenarios**:
  ```
  Scenario: 编排器逐行处理不中断
    Tool: Bash
    Steps:
      1. 运行 `pytest -q tests/test_orchestrator.py`
    Expected Result: tests pass
    Evidence: .sisyphus/evidence/task-10-orchestrator.txt
  ```

- [x] 11. 弹窗选择 CSV/音频目录/模板 event + 启动流程

  **What to do**:
  - 提供最小弹窗选择 CSV 与音频目录
  - 提供模板 event 选择（通过 FMOD 项目对象列表）
  - 启动后调用导入编排器

  **Must NOT do**:
  - 不增加复杂 UI

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3
  - **Blocks**: 12
  - **Blocked By**: 1,6

  **Acceptance Criteria**:
  - [x] pytest: UI 选择流程基础测试通过（可用 mock）

  **QA Scenarios**:
  ```
  Scenario: 选择 CSV 与音频目录后成功启动
    Tool: Bash
    Steps:
      1. 运行 `pytest -q tests/test_ui_flow.py`
    Expected Result: tests pass
    Evidence: .sisyphus/evidence/task-11-ui-flow.txt
  ```

- [x] 12. 端到端集成测试与示例数据

  **What to do**:
  - 提供示例 CSV + 音频目录样例（占位音频）
  - 提供 E2E 流程测试（mock FMOD 或在可用时运行）
  - 验证日志输出位置与汇总计数

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3
  - **Blocks**: —
  - **Blocked By**: 2,3,5,6,7,8,9,10,11

  **Acceptance Criteria**:
  - [x] pytest: E2E 样例流程通过

  **QA Scenarios**:
  ```
  Scenario: E2E 样例导入生成日志
    Tool: Bash
    Steps:
      1. 运行 `pytest -q tests/test_e2e.py`
    Expected Result: tests pass
    Evidence: .sisyphus/evidence/task-12-e2e.txt
  ```


---

## Final Verification Wave (MANDATORY — after ALL implementation tasks)

- [x] F1. **Plan Compliance Audit** — `oracle`
  Verify deliverables, guardrails, and evidence files. Output pass/fail per requirement.

- [x] F2. **Code Quality Review** — `unspecified-high`
  Run lint/tests; check for dead code, unsafe patterns, and log integrity.

- [x] F3. **Runtime QA** — `unspecified-high`
  Execute all QA scenarios end-to-end with FMOD running; collect evidence.

- [x] F4. **Scope Fidelity Check** — `deep`
  Ensure no extra features were added; all requirements satisfied.

---

## Commit Strategy

- **1**: `chore(scaffold): initialize batch import tool`
- **2**: `feat(csv): add parsing, defaults, and validation`
- **3**: `feat(fmod): add tcp client and template cloning`
- **4**: `feat(import): implement audio import pipeline + logging`
- **5**: `test(e2e): add integration fixtures`

---

## Success Criteria

### Verification Commands
```bash
pytest -q
```

### Final Checklist
- [x] CSV 样例与规范一致
- [x] 重名冲突自动重命名并记录
- [x] 日志文件生成在 CSV 同目录
- [x] FMOD TCP 驱动可稳定执行导入
