# Draft: FMOD 合并实施计划

## Requirements (confirmed)
- 将现有 5 份 FMOD 相关计划合并为 **一个完整实施计划**（按需要合并内容）。
- 合并后需 **全面 review 计划合理性**，重点核验 FMOD scripting API 的合法性、支持语法/格式，确保所有技术与依赖有据可查、无猜测。
- 按 **技术流程分步测试**，一个流程跑通后再进入下一个流程。
- 自动化测试必须包含；允许结合 FMOD console/log 做联调验证。
- 代码需在**当前工作区**从零重构（不依赖其他目录的现有实现）。
- FMOD Studio 版本固定为 2.02.07。
- 导入方式选择：**Create-only**（官方 API 创建 event/track/sound），不使用模板克隆。
- CSV 规范固定为 5 字段：`audio_path, event_path, asset_path, bus_path, bank_name`。
- 音频匹配规则采用计划中的严格规则（仅文件名、无扩展名匹配支持格式、递归、大小写敏感、重名字母序取第一个并警告）。
- 技术方案依赖选择：采用社区/主流成熟方案（由规划方确定具体库）。
- 测试策略：混合（纯逻辑 TDD；FMOD 联调部分 Tests-after）。
- 证据策略：脚本输出 + 二次验证（如读取/校验 FMOD 元数据或查询结果）。
- 运行方式：提供可双击的 `.bat` 脚本；不要求用户通过命令行手动输入命令。
- 不需要打包 exe；一切从简。
- 可用性要求：仅需保证本机可用（不要求通用环境适配）。
- 输入方式：双击 .bat 后使用**文件选择弹窗**提供 CSV / 音频目录 / 输出路径。
- 输出日志：Markdown 格式，固定放在 CSV 同目录。
- 外部仓库：以参考思路为主，若存在确定性高的可用函数可复用；确保来源可靠与合法。

## Technical Decisions
- 证据标准：以 **官方文档为准**，可参考社区实现方式作为补充佐证。
- 测试策略：必须包含自动化测试（具体 TDD/Tests-after 待定）。
- 测试策略选择：混合（纯逻辑 TDD；FMOD 联调 Tests-after）。
- 验证证据：脚本 JSON/结果 + 二次验证（不依赖人工转述为主）。
- 入口方式：双击 .bat 启动主流程（含必要 GUI 选择）。
- 分步测试顺序：从末端向前推进（先音频导入/事件创建/配置，再测模板或 CSV 匹配）。
- FMOD Console/日志获取方式尚不确定（可能需要人工提供日志文本）。

## Research Findings
- 代码库扫描：当前工作区仅包含 plans 与 draft 文档，未发现实际实现代码；计划引用的 src/* 目录仅存在于计划文本中（需另定位真实实现仓库）。
- 进一步扫描确认：当前工作区无 .py/.js/.ts 代码文件（greenfield）。
- 测试基础设施（来自相邻项目目录 `D:\WORKSPACE\Workspace\AD PJ\AI\Fmod Batch Import`）：pytest 已配置，存在多组 tests/ 与 debug/ 脚本；无 CI 配置。测试模式包含单元/集成/标记 slow。
- 用户提供外部参考仓库（待研究）：
  - https://github.com/synnys/fmod-bulk-importer
  - https://github.com/8ude/FMOD-Audio-Importer
  - https://github.com/momnus/FmodImporter
- 外部仓库抓取结果（已获取部分源码/README）：
  - **synnys/fmod-bulk-importer**：提供 FMOD Studio JS 脚本（`fmod-audio-importer working.js`），核心调用包括 `studio.project.create('Event')`、`event.addGroupTrack()`、`track.addSound(..., 'SingleSound'|'MultiSound'|'SoundScatterer')`、`studio.project.importAudioFile()`、`event.masterTrack.mixerGroup.effectChain.addEffect('SpatialiserEffect')`、`studio.project.create('EventFolder')`、`studio.system.readDir()`、`studio.ui.showModalDialog()`、`studio.system.getFile()` 写日志。采用“按文件名后缀决定事件类型”的规则并跳过已存在事件。
  - **8ude/FMOD-Audio-Importer**：C# WPF 客户端 + Telnet 连接 3663 发送 JS 行；JS 使用 `studio.project.model.Event.findInstances()` 查重、`studio.project.create('Event')` + `addGroupTrack` + `addSound`、`SingleSound`/`MultiSound`/`SoundScatterer`、`sound.audioFile` 与 `sound.length`；支持 `SpatialiserEffect`。拖拽文件夹导入并按后缀生成事件。
  - **momnus/FmodImporter**：C# WPF 客户端 + Telnet；引入“全局 JS 脚本 + 分组脚本模板”的模式；先批量 `importAudioFile`，再按分组生成事件/文件夹；使用 `studio.project.filePath` 读取项目路径（解析 `out():` 前缀）；每组脚本末尾保存 `studio.project.save()`；详细日志与状态回传。
- FMOD 官方文档抓取失败（webfetch 返回空/连接中断），需改用浏览器或用户提供可访问的官方文档来源（用于合法性证据）。
- **FMOD 官方文档证据（已通过浏览器获取）**：
  - *Scripting Terminal*：FMOD Studio 支持通过 **TCP 3663** 执行 JavaScript（UTF‑8 编码）；接收的数据视为 JS，返回 UTF‑8 字符串；控制台可在 Window > Console 打开（Scripting 章节）。
  - *Project API*：`studio.project.create(entityName)` 创建对象；`project.importAudioFile(filePath)` 需要 **绝对路径**，失败返回 null；`project.lookup(idOrPath)` 支持 GUID 或 `type:/path`（type 包括 event/bank/bus/vca/asset 等）；`project.filePath` 提供 .fspro 绝对路径。
  - *Event API*：`Event.addGroupTrack(name)` 创建音轨并返回 GroupTrack。
  - *Track API*：`GroupTrack.addSound(parameter, soundType, start, length)`；soundType 必须是 `SingleSound`/`MultiSound`/`ProgrammerSound`。
  - *Sound API*：存在 `model.SingleSound` / `model.MultiSound` / `model.SoundScatterer` 等类型；多音轨例子使用 `studio.project.create('SingleSound')` 并设置 `audioFile` 与 `owner`。
  - *Folder API*：`workspace.masterAssetFolder.getAsset(path)` 与 `folder.getItem(path)` 支持按相对路径获取。
  - *Workspace API*：`workspace.addEvent(name, withSpatializer)` 可直接创建 event 并可选择 spatializer。
  - *Managing Assets*：可导入的音频扩展名包括 `.wav .mp3 .ogg .aif .aiff .wma .flac`。
  - *ManagedObject API*：ManagedObject 由 `id/entity/properties/relationships` 组成；`relationships` 支持 ToOne/ToMany（ToMany 需用 `relationships.<name>.add/insert/remove`）；`ManagedRelationship.add` 成功返回 true；`ManagedObject.isValid` 判断对象有效性。
- **未完整抓取的官方页面**（仍需补证据）：
  
- **用户提供截图证据（官方页面）**：
  - `Project.Model.Bank` 页面显示：
    - `model.Bank` 描述为 *A collection of model.Events to build into a binary file, to be loaded by the FMOD Studio API.*
    - `Bank.getPath()`：*Retrieves the bank's unique path identifier.* 返回 `path` 字符串。
  - `Project.Model.MixerStrip` 页面显示：
    - 类型包括 `model.EventMixerGroup`、`model.EventMixerMaster`、`model.EventMixerReturn`、`model.MixerBus`、`model.MixerGroup`、`model.MixerInput`、`model.MixerMaster`、`model.MixerPort`、`model.MixerReturn`、`model.MixerStrip`、`model.MixerVCA`。
    - 扩展方法：`MixerBus.getInputFormat()`、`MixerBus.getOutputFormat()`、`MixerStrip.getPath()`；`MixerStrip.getPath()` 返回 mixer strip 的路径字符串。

## Open Questions
- 需要合并的范围：是否包含所有 5 份计划（voiceover / bugfix / audio-resolution / scripting-probe / main-flow-fix）且不删减？
- FMOD Studio 版本是否固定为 2.02.07？
- 可接受的“证据来源”范围：仅官方文档 vs 官方文档 + 现有代码实现 vs 官方 + 高质量开源示例。
- 测试策略：TDD / Tests-after / 无自动化测试？
- 分步测试的“技术流程顺序”是否有既定顺序？
- 实际代码仓库位置：是否在 `D:\WORKSPACE\Workspace\AD PJ\AI\Fmod Batch Import`？若不是，请提供路径。
- FMOD Console/日志可否自动化获取（文件日志路径或可导出）？若不可，是否允许人工提供日志文本作为证据？
- Import 方案取舍：模板克隆（继承现有参数） vs create-only（官方 API 创建） vs 可选两种模式？
- CSV 规范是否固定为 5 字段（audio_path, event_path, asset_path, bus_path, bank_name）？
- 音频匹配规则（大小写敏感/扩展名/子目录）是否采用计划中的严格规则？
- 技术栈/依赖约束（Python 版本、是否允许新增依赖）。
- 测试策略选择：TDD 还是 Tests-after？
- 验证证据来源：若无法自动读取 FMOD Console/日志，是否允许以脚本返回的 JSON/结果作为验证证据（不依赖人工转述）？
- 是否仍需“可双击运行”的入口与最小 UI（tkinter 文件选择）？
- Python 版本/打包方式是否有约束（例如 3.10+，是否需要生成 exe）？
- 是否可假设目标机器已安装 Python 且可被 .bat 调用？若不能，需要怎样的最低安装要求说明？

## Scope Boundaries
- INCLUDE: 合并全部相关计划内容 + API 合法性核验 + 流程分步测试策略。
- EXCLUDE: 未经证据支持的 API/语法/流程（若无法证实将标注为需决策或移除）。
