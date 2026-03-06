# FMOD CSV Batch Importer

**中文** | [English](#english)

---

## 中文

### 项目简介

通过 CSV 文件批量向 FMOD Studio 导入音频事件的命令行工具。工具通过 FMOD Studio 的 TCP 脚本接口（端口 3663）与 FMOD 通信，无需手动逐条创建事件，适合大量音频资源的批量处理场景。

### 功能特性

- **批量创建事件**：从 CSV 一次性导入任意数量的音频事件
- **自动挂载音频**：将音频文件导入 FMOD 资源库并关联到对应事件
- **Bus / Bank 分配**：支持为每个事件指定输出 Bus 和所属 Bank
- **模板事件继承**：可指定模板事件，自动继承其 Bus / Bank 配置
- **自动创建文件夹**：Event 路径中的多级目录不存在时自动创建
- **跳过已存在事件**：重复运行安全，不会覆盖已有事件
- **实时终端进度**：导入过程中逐行显示状态（OK / SKIP / FAIL / WARN）
- **Markdown 日志**：每次运行生成带时间戳的详细日志文件
- **路径记忆**：GUI 自动记住上次使用的文件路径

### 环境要求

- Python 3.10+
- FMOD Studio 2.02+（需开启脚本服务器）

### 安装

```bash
# 克隆仓库
git clone https://github.com/Gaaaamu/fmod-csv-batch-importer.git
cd fmod-csv-batch-importer

# 安装依赖（仅测试需要）
pip install pytest pytest-cov
```

### 使用方法

#### 1. 开启 FMOD Studio 脚本服务器

在 FMOD Studio 中：`Edit → Preferences → Scripting → Enable Scripting` ✓

#### 2. 准备 CSV 文件

CSV 必须包含以下 5 列（顺序固定）：

| 列名 | 说明 | 是否必填 |
|------|------|----------|
| `audio_path` | 音频文件名（相对于音频目录） | ✅ |
| `event_path` | FMOD 事件路径，如 `event:/VO/hero_01` | ✅ |
| `asset_path` | 资源库中的子目录路径，如 `VO/hero` | 可为空 |
| `bus_path` | 输出 Bus，如 `bus:/VO` | 可为空 |
| `bank_name` | 所属 Bank，如 `bank:/VO` | 可为空 |

示例 CSV：

```csv
audio_path,event_path,asset_path,bus_path,bank_name
hero_01.wav,event:/VO/Hero/hero_01,VO/Hero,bus:/VO,bank:/VO
hero_02.wav,event:/VO/Hero/hero_02,VO/Hero,bus:/VO,bank:/VO
sfx_jump.wav,event:/SFX/jump,,bus:/SFX,
```

路径前缀可省略，工具会自动补全（`event:/`、`bus:/`、`bank:/`）。

#### 3. 启动工具

**方式一：双击 bat 文件（Windows）**

```
run_import.bat
```

**方式二：命令行**

```bash
python -m fmod_batch_import
```

#### 4. 在 GUI 中填写参数

| 字段 | 说明 |
|------|------|
| CSV File | 选择准备好的 CSV 文件 |
| Audio Directory | 选择音频文件所在的根目录 |
| Template Event Path | （可选）用于继承 Bus / Bank 的模板事件路径 |

点击 **Run Import** 开始，终端会实时输出每行的处理结果。

### 工作流说明

```
CSV 文件
    │
    ▼
[Phase 1] Python 预处理
    • 解析 CSV，校验字段
    • 规范化路径（补全前缀）
    • 在文件系统中定位音频文件
    • 路径或文件错误 → 立即标记为 FAIL，终端输出
    │
    ▼
[Phase 2] 单次批量 TCP 调用
    • 将所有有效行打包为一个 JS 函数发送给 FMOD
    • FMOD 内部逐行处理：
        1. 检查事件是否已存在（已存在 → SKIP）
        2. 导入音频文件，按 asset_path 归档
        3. 创建事件，添加 GroupTrack 和 SingleSound
        4. 分配 Bus（找不到 → 警告并继续）
        5. 分配 Bank（找不到 → 警告并继续）
        6. 将事件移入目标文件夹（自动创建缺失层级）
    • 返回逐行结果数组
    │
    ▼
[Phase 3] 保存 & 记录
    • 调用 studio.project.save()
    • 写入 Markdown 日志（与 CSV 文件同目录）
    • 终端输出汇总：N ok, N skip, N fail
```

### 终端输出示例

```
[Import] 4 row(s) loaded from CSV
[Import] Sending 4 row(s) to FMOD...
[  OK  ] Row 1 | event:/VO/Hero/hero_01 | hero_01.wav
[  OK  ] Row 2 | event:/VO/Hero/hero_02 | hero_02.wav (1 warning(s))
[ WARN ] Row 2 | Bus not found: bus:/VO
[ SKIP ] Row 3 | event:/SFX/jump | sfx_jump.wav
[ FAIL ] Row 4 | event:/SFX/land | sfx_land.wav | importAudioFile null
[Import] Saving project...
[Import] Done — 2 ok, 1 skip, 1 fail
[Import] Log: C:\Project\audio\template_20260306_120000_log.md
```

### 注意事项

- 工具运行前 FMOD Studio 必须处于**打开且已加载项目**的状态
- TCP 端口固定为 **3663**，请确保无防火墙拦截
- 目标版本：**FMOD Studio 2.02+**，不兼容更早版本
- 每次运行固定 **2 次 TCP 调用**（1 次批量 + 1 次保存），与行数无关

---

<a name="english"></a>

## English

### Overview

A tool for batch-importing audio events into FMOD Studio from a CSV file. It communicates with FMOD Studio via the TCP scripting API (port 3663), eliminating the need to create events one by one. Suitable for projects with large volumes of audio assets.

### Features

- **Batch event creation** — import any number of audio events from a single CSV
- **Automatic audio linking** — imports audio files into the asset library and links them to events
- **Bus / Bank assignment** — specify output bus and bank per event
- **Template event inheritance** — inherit Bus / Bank config from an existing template event
- **Auto folder creation** — missing parent folders in event paths are created automatically
- **Skip existing events** — safe to re-run; existing events are skipped, not overwritten
- **Real-time terminal progress** — per-row status printed as import runs (OK / SKIP / FAIL / WARN)
- **Markdown log** — timestamped log file written after every run
- **Path memory** — GUI remembers last-used file paths

### Requirements

- Python 3.10+
- FMOD Studio 2.02+ (with scripting server enabled)

### Installation

```bash
git clone https://github.com/Gaaaamu/fmod-csv-batch-importer.git
cd fmod-csv-batch-importer

# Install dev dependencies (tests only)
pip install pytest pytest-cov
```

### Usage

#### 1. Enable the FMOD Studio scripting server

In FMOD Studio: `Edit → Preferences → Scripting → Enable Scripting` ✓

#### 2. Prepare a CSV file

The CSV must have exactly these 5 columns in this order:

| Column | Description | Required |
|--------|-------------|----------|
| `audio_path` | Audio filename relative to the audio directory | ✅ |
| `event_path` | FMOD event path, e.g. `event:/VO/hero_01` | ✅ |
| `asset_path` | Asset browser subfolder, e.g. `VO/hero` | optional |
| `bus_path` | Output bus, e.g. `bus:/VO` | optional |
| `bank_name` | Bank assignment, e.g. `bank:/VO` | optional |

Path prefixes (`event:/`, `bus:/`, `bank:/`) are optional — they will be added automatically.

#### 3. Run the tool

**Windows (double-click):**
```
run_import.bat
```

**Command line:**
```bash
python -m fmod_batch_import
```

#### 4. Fill in the GUI

| Field | Description |
|-------|-------------|
| CSV File | Path to your CSV file |
| Audio Directory | Root folder containing your audio files |
| Template Event Path | (Optional) An existing event to inherit Bus / Bank from |

Click **Run Import**. Progress is printed to the terminal in real time.

### How It Works

The import runs in two phases:

1. **Python preprocessing** — parse CSV, validate paths, locate audio files on disk. Rows with missing audio or invalid paths are marked as `FAIL` immediately.

2. **Single batch TCP call** — all valid rows are packed into one JavaScript function and sent to FMOD in a single call. FMOD processes each row: duplicate check → audio import → event creation → track/sound setup → bus/bank assignment → folder placement. Returns a per-row result array.

Then the project is saved and a Markdown log is written next to the CSV file. Total TCP calls: **2** (batch + save), regardless of row count.

### Notes

- FMOD Studio must be **open with a project loaded** before running the tool
- TCP port is fixed at **3663**
- Target: **FMOD Studio 2.02+** — not compatible with earlier versions
- `studio.project.create('EncodableAsset')` is broken in FMOD 2.02+ and is not used

### Running Tests

```bash
python -m pytest tests/
python -m pytest --cov=fmod_batch_import tests/
```
