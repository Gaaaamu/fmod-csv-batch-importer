# FMOD 批量导入工具：连接崩溃修复 + 工程选择增强

## TL;DR

> **Quick Summary**: 修复 `FMODClient.connect()` 缺失导致的启动崩溃，并新增“选择 .fspro 工程 → 自动启动 FMOD Studio 打开工程”的流程，解决多实例/工程选择问题。
>
> **Deliverables**:
> - `FMODClient.connect()` 连接检查
> - 工程选择对话框（.fspro）与自动启动 FMOD
> - 连接失败提示与日志
>
> **Estimated Effort**: Short
> **Parallel Execution**: YES — 2 waves
> **Critical Path**: FMOD 启动策略 → connect 修复 → UI 工程选择 → 入口流程更新

---

## Context

### Original Request
用户运行工具时报错：`AttributeError: 'FMODClient' object has no attribute 'connect'`。同时希望能选择 FMOD 工程文件（.fspro）并自动启动 FMOD 打开该工程，以避免多开 FMOD 实例造成的不确定连接。

### Interview Summary
**Key Discussions**:
- 修复 `FMODClient.connect` 缺失导致的启动崩溃。
- 增加弹窗选择 .fspro，并自动启动 FMOD 打开工程。
- 选择策略：**A. 选 .fspro → 自动启动 FMOD 并打开该工程**。

**Research Findings**:
- FMOD Studio 脚本接口默认使用 TCP 3663。
- CLI 允许 `fmodstudio "path.fspro"` 打开工程。

### Metis Review
**Identified Gaps (addressed)**:
- 需要明确 FMOD Studio 可执行路径来源（手动选择/环境变量/默认路径）。
- 连接失败时提示与重试策略需明确。
- 多实例端口无法自动区分（默认只连 3663）。

---

## Work Objectives

### Core Objective
修复连接崩溃，并增加工程选择 + 自动启动流程，确保用户可以可靠连接到正确 FMOD 工程。

### Concrete Deliverables
- `FMODClient.connect()` 实现（连接性测试）
- 工程选择对话框（选择 .fspro）
- 启动 FMOD Studio 并打开工程
- 连接失败清晰提示

### Definition of Done
- [x] 启动/退出不再出现 `AttributeError: connect/close`
- [x] 可选择 .fspro 并自动打开 FMOD 工程
- [x] 连接失败有明确错误提示

### Must Have
- 不引入新依赖
- 使用 tkinter 维持 UI 风格
- 若用户取消选择工程，必须安全退出

### Must NOT Have (Guardrails)
- 不改变 CSV 解析/导入逻辑
- 不引入复杂配置管理
- 不做多实例端口扫描

---

## Verification Strategy

### Test Decision
- **Automated tests**: Tests-after (补测试)
- **Framework**: pytest

### QA Policy
所有验证必须可脚本化运行，不依赖人工手动。

---

## Execution Strategy

### Parallel Execution Waves

Wave 1
├── Task 1: FMODClient.connect 实现与测试
├── Task 2: UI 增加工程选择对话框
└── Task 3: FMOD Studio 启动策略（可执行路径选择）

Wave 2
├── Task 4: 更新 main 启动流程（工程选择 + 自动启动 + 连接）
└── Task 5: 端到端验证与日志输出

---

## TODOs

- [x] 1. 添加 `FMODClient.connect()` 方法

  **What to do**:
  - 在 `src/fmod_batch_import/fmod_client.py` 中增加 `connect()`，进行 socket 连接性测试
  - 连接成功后立即关闭 socket
  - 返回 True/无异常即为成功
  - 增加 `close()`（可为 no-op）以避免 main 中调用报错

  **QA Scenarios**:
  ```
  Scenario: connect 成功时不报错
    Tool: Bash
    Steps:
      1. pytest -q tests/test_fmod_client.py
    Expected Result: tests pass
  ```
  ```
  Scenario: close 存在且无异常
    Tool: Bash
    Steps:
      1. pytest -q tests/test_fmod_client.py
    Expected Result: tests pass
  ```

- [x] 2. 添加 .fspro 选择对话框

  **What to do**:
  - 在 `src/fmod_batch_import/ui.py` 添加 `select_project_file()`，只允许 .fspro
  - 返回 Path 或 None

  **QA Scenarios**:
  ```
  Scenario: 项目文件选择函数存在
    Tool: Bash
    Steps:
      1. pytest -q tests/test_ui.py
    Expected Result: tests pass
  ```

- [x] 3. 实现 FMOD Studio 启动逻辑

  **What to do**:
  - 新建 `src/fmod_batch_import/launcher.py`，新增 `launch_fmod(project_path, fmod_exe_path=None)`
  - Windows 默认路径不可用时提示用户选择 FMOD Studio.exe
  - 启动后等待短暂延迟（2-3 秒）再尝试 connect

  **QA Scenarios**:
  ```
  Scenario: 启动命令生成正确
    Tool: Bash
    Steps:
      1. pytest -q tests/test_launcher.py
    Expected Result: tests pass
  ```

- [x] 4. 更新 main 入口流程

  **What to do**:
  - 更新 `src/fmod_batch_import/__main__.py` 增加 .fspro 选择步骤
  - 若选择工程 → 启动 FMOD → connect
  - 若取消 → 退出并提示

  **QA Scenarios**:
  ```
  Scenario: main 流程启动不报错
    Tool: Bash
    Steps:
      1. pytest -q tests/test_main.py
    Expected Result: tests pass
  ```

- [x] 5. 端到端验证

  **What to do**:
  - Mock FMOD 启动与连接
  - 验证失败时有清晰错误信息

  **QA Scenarios**:
  ```
  Scenario: 连接失败提示
    Tool: Bash
    Steps:
      1. pytest -q tests/test_integration.py
    Expected Result: tests pass
  ```

---

## Final Verification Wave

- [x] F1. Plan Compliance Audit
- [x] F2. Code Quality Review (pytest)
- [x] F3. Runtime QA (mocked)
- [x] F4. Scope Fidelity Check

---

## Commit Strategy
- `fix(connect): add FMODClient.connect`
- `feat(ui): select fspro project`
- `feat(launch): start FMOD Studio`
- `feat(main): integrate project selection and connect`

---

## Success Criteria
- [x] 启动/退出不会出现 AttributeError（connect/close）
- [x] 用户可选择工程并打开
- [x] 连接失败有明确提示
