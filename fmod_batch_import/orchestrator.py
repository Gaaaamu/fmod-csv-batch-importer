"""
Orchestrator for FMOD Batch Import.

Drives the full CSV-to-FMOD import pipeline in two phases:

  Phase 1 (Python): Parse CSV → normalize paths → resolve audio files.
  Phase 2 (FMOD):   Send ONE batch JS call that processes all rows internally.
                    Returns per-row results array (~2 TCP calls total).

Rules:
- If event_path already exists in FMOD: skip row
- If bus/bank not found: warn + continue (no bus/bank assigned)
- If TCP connection fails: abort entire batch
- Any other row error: log failure, continue to next row
"""

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

from fmod_batch_import.csv_parser import CSVReader, CSVParseError, CSVRow
from fmod_batch_import.audio_resolver import AudioResolver
from fmod_batch_import.path_normalizer import PathNormalizer
from fmod_batch_import.log_writer import LogWriter
from fmod_batch_import.fmod_client import FMODClient, FMODConnectionError
from fmod_batch_import.js_builder import js_batch_process, js_save
from fmod_batch_import.template_inspector import inspect_template_event


@dataclass
class RowResult:
    row_index: int
    status: str  # "success" | "skip" | "fail"
    event_path: str = ""
    audio_path: str = ""
    message: str = ""


@dataclass
class BatchSummary:
    success: int = 0
    skip: int = 0
    fail: int = 0
    total: int = 0
    rows: list[RowResult] = field(default_factory=list)


class Orchestrator:
    """
    Drives the full CSV-to-FMOD import pipeline.

    Args:
        csv_path: Path to the CSV file.
        audio_dir: Directory to search for audio files.
        fmod_client: Connected FMODClient instance.
        log_writer: Optional LogWriter; if None, one is created next to CSV.
        template_event_path: Optional template event path for bus/bank inheritance.
    """

    def __init__(
        self,
        csv_path: str,
        audio_dir: str,
        fmod_client: FMODClient,
        log_writer: LogWriter | None = None,
        template_event_path: str | None = None,
    ):
        self.csv_path: str = csv_path
        self.audio_dir: str = audio_dir
        self.client: FMODClient = fmod_client
        csv_abs = Path(os.path.abspath(csv_path))
        self.csv_dir: Path = csv_abs.parent
        self.log_writer: LogWriter = log_writer or LogWriter(
            output_dir=self.csv_dir,
            csv_filename=csv_abs.name,
        )
        
        # Get template info for inheritance (bus/bank defaults)
        template_bus_path = None
        template_bank_name = None
        if template_event_path:
            template_info = inspect_template_event(fmod_client, template_event_path)
            template_bus_path = template_info.bus_path
            template_bank_name = template_info.bank_name
            self.template_event_id: str | None = template_info.event_id
        else:
            self.template_event_id = None
        
        self._csv_reader: CSVReader = CSVReader()
        self._audio_resolver: AudioResolver = AudioResolver(Path(str(audio_dir)))
        self._path_normalizer: PathNormalizer = PathNormalizer(
            audio_dir=str(audio_dir),
            template_event_path=template_event_path,
            template_bus_path=template_bus_path,
            template_bank_name=template_bank_name,
            event_folder_supported=True,  # js_ensure_folder_and_move auto-creates missing folders
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> BatchSummary:
        """Execute the full batch import. Returns a BatchSummary.

        Two-phase approach:
        1. Python preprocesses all rows (normalize paths, resolve audio files).
        2. One TCP call sends a batch JS function covering all rows.
           Per-row results (success/skip/fail + warnings) are returned as an array.
        """
        summary = BatchSummary()

        # --- Phase 0: Parse CSV ---
        try:
            rows: list[CSVRow] = self._csv_reader.read_file(self.csv_path)
        except (CSVParseError, FileNotFoundError) as exc:
            raise ValueError(f"CSV error: {exc}") from exc

        summary.total = len(rows)
        print(f"[Import] {len(rows)} row(s) loaded from CSV")

        # --- Phase 1: Python preprocessing ---
        prepped_rows: list[dict[str, object]] = []  # rows ready for JS processing
        all_results: list[RowResult] = []  # pre-failed rows (path/audio errors)

        for csv_row in rows:
            idx = csv_row.row_index
            audio_name = csv_row.audio_path.strip()
            event_path_raw = csv_row.event_path.strip()
            bank_name_original = csv_row.bank_name.strip()

            # Normalize paths
            try:
                norm = self._path_normalizer.normalize_row(
                    audio_path=audio_name,
                    event_path=event_path_raw,
                    asset_path=csv_row.asset_path.strip(),
                    bus_path=csv_row.bus_path.strip(),
                    bank_name=bank_name_original,
                    row_index=idx,
                )
            except Exception as exc:
                msg = f"Path error: {exc}"
                print(f"[ FAIL ] Row {idx} | {audio_name} | {msg}")
                all_results.append(
                    RowResult(idx, "fail", event_path_raw, audio_name, msg)
                )
                continue

            # Resolve audio file (filesystem check in Python)
            try:
                audio_abs = self._audio_resolver.resolve(audio_name)
            except FileNotFoundError as exc:
                print(f"[ FAIL ] Row {idx} | {audio_name} | {exc}")
                all_results.append(
                    RowResult(idx, "fail", norm.event_path, audio_name, str(exc))
                )
                continue

            # Compute asset relative path for setAssetPath()
            asset_rel_path: str | None = None
            try:
                asset_rel_path = str(
                    audio_abs.relative_to(Path(self.audio_dir))
                ).replace("\\", "/")
            except ValueError:
                pass  # audio file outside audio_dir — import to Assets root

            # Determine bank strategy:
            # use_template_banks=True  → copy all banks from template event GUID
            # use_template_banks=False + bank_name non-empty → assign specific bank
            # both empty → no bank assignment
            use_template_banks = (
                bank_name_original == "" and self.template_event_id is not None
            )

            prepped_rows.append({
                "row_index": idx,
                "audio_abs_path": str(audio_abs).replace("\\", "/"),
                "asset_rel_path": asset_rel_path,
                "event_path": norm.event_path,
                "audio_name": audio_name,
                "bus_path": norm.bus_path,
                "bank_name": norm.bank_name,
                "use_template_banks": use_template_banks,
                "folder_path": self._get_event_folder_path(norm.event_path),
            })

        # --- Phase 2: Single batch JS call ---
        if prepped_rows:
            print(f"[Import] Sending {len(prepped_rows)} row(s) to FMOD...")
            try:
                batch_result = self._exec(
                    js_batch_process(prepped_rows, self.template_event_id)
                )
            except FMODConnectionError:
                raise  # Abort entire batch on TCP failure

            if not batch_result.get("ok"):
                raise ValueError(
                    f"Batch JS execution failed: {batch_result.get('error')}"
                )

            js_results_raw = batch_result.get("results", [])
            if isinstance(js_results_raw, list):
                for item in js_results_raw:
                    if not isinstance(item, dict):
                        continue
                    row_idx_raw = item.get("row_index", 0)
                    row_idx = row_idx_raw if isinstance(row_idx_raw, int) else 0
                    status = str(item.get("status", "fail"))
                    ep = str(item.get("event_path", ""))
                    an = str(item.get("audio_name", ""))
                    msg = str(item.get("message", ""))
                    warnings_raw = item.get("warnings", [])
                    all_results.append(RowResult(row_idx, status, ep, an, msg))

                    # --- Terminal output per row ---
                    if status == "success":
                        warn_count = len(warnings_raw) if isinstance(warnings_raw, list) else 0
                        suffix = f" ({warn_count} warning(s))" if warn_count else ""
                        print(f"[  OK  ] Row {row_idx} | {ep} | {an}{suffix}")
                    elif status == "skip":
                        print(f"[ SKIP ] Row {row_idx} | {ep} | {an}")
                    else:
                        print(f"[ FAIL ] Row {row_idx} | {ep} | {an} | {msg}")

                    if isinstance(warnings_raw, list):
                        for w in warnings_raw:
                            print(f"[ WARN ] Row {row_idx} | {w}")
                            self.log_writer.add_warning(f"Row {row_idx}: {w}")

        # --- Phase 3: Sort by row order, aggregate, and log ---
        all_results.sort(key=lambda r: r.row_index)

        for result in all_results:
            summary.rows.append(result)
            if result.status == "success":
                summary.success += 1
            elif result.status == "skip":
                summary.skip += 1
            else:
                summary.fail += 1

            self.log_writer.log_row(
                row_num=result.row_index,
                audio_file=result.audio_path,
                event_path=result.event_path,
                status=result.status,
                message=result.message,
            )

        # Save project (best-effort)
        print("[Import] Saving project...")
        try:
            _ = self._exec(js_save())
        except FMODConnectionError:
            pass

        log_path = self.log_writer.write()
        print(f"[Import] Done — {summary.success} ok, {summary.skip} skip, {summary.fail} fail")
        print(f"[Import] Log: {log_path}")
        return summary

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _exec(self, js: str) -> dict[str, object]:
        """
        Execute JS via FMODClient and parse JSON response.
        Raises FMODConnectionError on connection failure (propagated from FMODClient).
        """
        response = self.client.execute(js)
        # Extract JSON from out(): lines
        # FMOD response format: log(): ...\n\0out(): {json}\n\n\0
        match = re.search(r'out\(\):\s*(\{.*\})', response, re.DOTALL)
        if match:
            json_str = match.group(1).strip()
        else:
            json_str = response.strip()
        try:
            data = cast(object, json.loads(json_str))
            if isinstance(data, dict):
                return cast(dict[str, object], data)
            return {"ok": False, "error": "Non-dict JSON response"}
        except json.JSONDecodeError:
            return {"ok": False, "error": f"Non-JSON response: {response[:200]}"}

    @staticmethod
    def _get_event_folder_path(event_path: str) -> str | None:
        if "/" not in event_path:
            return None
        folder_path, _ = event_path.rsplit("/", 1)
        if folder_path in ("event:", "event:/"):
            return None
        return folder_path


