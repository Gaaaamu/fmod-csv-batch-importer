# AGENTS.md — FMOD Batch Import

Guidance for AI coding agents working in this repository.

**语言**：始终使用中文与用户交流。

---

## Project Overview

Python tool that batch-imports audio events into FMOD Studio from a CSV file.
Communicates with FMOD Studio via TCP scripting API (port 3663, JavaScript strings).

**Main package**: `fmod_batch_import/`  
**Entry point**: `fmod_batch_import/__main__.py`  
**Key modules**: `orchestrator.py`, `js_builder.py`, `fmod_client.py`, `csv_parser.py`  
**Tests**: `tests/` (pytest, 99 tests)

---

## Commands

```bash
# Run all tests
python -m pytest tests/

# Run a single test file
python -m pytest tests/test_orchestrator.py

# Run a single test by name
python -m pytest tests/test_orchestrator.py::TestOrchestratorSuccess::test_single_row_success

# Run with coverage
python -m pytest --cov=fmod_batch_import tests/

# Run the tool
python -m fmod_batch_import
```

No linter or formatter is configured (`pyproject.toml` has no ruff/black/mypy sections).
Target Python: **3.10+**. Use 3.10+ syntax everywhere.

---

## Architecture

The import pipeline runs in two phases inside `Orchestrator.run()`:

1. **Phase 1 (Python)**: Parse CSV → normalize paths → resolve audio files on disk.  
   Rows that fail here (missing audio, bad path) are marked `fail` immediately.
2. **Phase 2 (FMOD)**: ONE batch JS call handles all remaining rows internally.  
   Returns a per-row results array. Followed by ONE save call.  
   Total TCP calls: **2** (batch + save), regardless of row count.

`js_builder.py` generates all JavaScript as self-executing IIFEs embedded in Python f-strings.  
All JS returns `JSON.stringify({ok: bool, ...})` so Python can parse it uniformly.

---

## Code Style

### Imports
Standard library → blank line → third-party → blank line → local package.  
Use `from __future__ import annotations` only when a file already has it (e.g. `csv_parser.py`).

```python
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

from fmod_batch_import.csv_parser import CSVReader, CSVParseError, CSVRow
from fmod_batch_import.fmod_client import FMODClient, FMODConnectionError
```

### Type Annotations
- Always annotate function parameters and return types.
- Use **3.10+ union syntax**: `X | None`, not `Optional[X]`.
- Use **built-in generics**: `list[str]`, `dict[str, object]`, not `List`, `Dict`.
- `cast()` is acceptable when narrowing after isinstance checks.

```python
def normalize_row(self, audio_path: str, event_path: str) -> NormResult: ...
def _exec(self, js: str) -> dict[str, object]: ...
log_writer: LogWriter | None = None
asset_rel_path: str | None = None
```

### Naming
| Kind | Style | Example |
|---|---|---|
| Functions / methods | `snake_case` | `normalize_row`, `read_file` |
| Private helpers | `_snake_case` | `_exec`, `_esc`, `_get_event_folder_path` |
| Classes | `PascalCase` | `Orchestrator`, `FMODClient`, `BatchSummary` |
| Constants | `SCREAMING_SNAKE_CASE` | `EXPECTED_COLUMNS` |
| Variables | `snake_case` | `prepped_rows`, `audio_abs` |

### Data Structures
- `@dataclass` for mutable result/summary objects (`RowResult`, `BatchSummary`).
- `NamedTuple` for immutable row data (`CSVRow`).
- No `TypedDict` in use — plain `dict[str, object]` for JS payload dicts.

```python
@dataclass
class RowResult:
    row_index: int
    status: str  # "success" | "skip" | "fail"
    event_path: str = ""
    message: str = ""
```

### Error Handling
- Define custom exceptions inheriting from `Exception` with a one-line docstring.
- Always chain with `raise X from exc`.
- Catch the **most specific** exception type available.
- Use `elif`, never `else: if`.

```python
class FMODConnectionError(Exception):
    """Raised when FMOD TCP connection is lost or unavailable."""

try:
    rows = self._csv_reader.read_file(self.csv_path)
except (CSVParseError, FileNotFoundError) as exc:
    raise ValueError(f"CSV error: {exc}") from exc
```

### Docstrings & Comments
- Module-level docstring at top of every file (multi-line for complex modules).
- Class docstring: describe purpose + `Args:` for `__init__` params.
- Public method docstring: one-liner or Google-style with `Args:` / `Returns:` / `Raises:`.
- Private helpers: one-line docstring only.
- Inline comments: `# --- Section Name ---` dividers for logical blocks inside long methods.

```python
def execute(self, js_code: str) -> str:
    """Execute JS code via FMOD TCP scripting API.

    Raises:
        FMODConnectionError: If connection cannot be established or is lost.
    """
```

### String Formatting
Use **f-strings exclusively**. No `.format()`, no `%`.

### Conditionals
Use `elif` for mutually exclusive branches — never `else: if`.

```python
if result.status == "success":
    summary.success += 1
elif result.status == "skip":
    summary.skip += 1
else:
    summary.fail += 1
```

---

## JS Builder Conventions (`js_builder.py`)

- Every public function is named `js_<verb>_<noun>` and returns a `str`.
- All JS is a self-executing IIFE: `(function(){ ... })();`
- All JS returns `JSON.stringify({ok: bool, ...})`.
- String values embedded in JS must be escaped via `_esc()`.
- Inline Python comments inside the JS string explain each JS step:

```python
def js_save() -> str:
    """Generate JS to save the project."""
    return "studio.project.save();"

def js_lookup(event_path: str) -> str:
    safe = _esc(event_path)
    return (
        f"(function(){{"
        f"var obj=studio.project.lookup('{safe}');"
        f"if(!obj)return JSON.stringify({{ok:false}});"
        f"return JSON.stringify({{ok:true,id:obj.id}});"
        f"}})();"
    )
```

---

## Test Conventions (`tests/`)

- Test files: `test_<module>.py`. Test classes: `Test<Feature>`. Test functions: `test_<scenario>`.
- Helper functions in each file follow `_make_<thing>` naming and are private to that file.
- Mock `FMODClient` via `MagicMock` with `side_effect` list — **never** connect to real FMOD in tests.
- Mock response sequence mirrors exact TCP call order: `[batch_response, "ok"]` (batch → save).
- Assert `client.execute.call_count` when the exact number of TCP calls matters.
- Use `pytest.raises(ExceptionType)` for expected exceptions.
- `tmp_path` fixture (pytest built-in) for all temporary files.

```python
def _mock_client(responses: list) -> MagicMock:
    client = MagicMock()
    client.execute.side_effect = [json.dumps(r) for r in responses]
    return client

def test_tcp_failure_aborts_batch(self, tmp_path):
    client = MagicMock()
    client.execute.side_effect = FMODConnectionError("lost")
    with pytest.raises(FMODConnectionError):
        Orchestrator(csv_path, audio_dir, client).run()
```

---

## Critical Rules

- **Do not suppress type errors** with `cast`, `# type: ignore`, or `Any` without a comment explaining why.
- **Do not refactor while fixing bugs** — minimal, targeted changes only.
- **Do not commit** unless explicitly asked.
- **Do not change the TCP call count** without updating test mocks accordingly.
- FMOD JS API calls must be verified against the real FMOD console before adding new ones — the API is undocumented and version-sensitive (target: FMOD Studio 2.02+).
- `studio.project.create('EncodableAsset')` is **broken** in FMOD 2.02+ — do not use.
- Asset subfolder "unimported" badge: known cosmetic issue, intentionally not fixed.
