"""
Orchestrator for FMOD Batch Import.

Drives the full CSV-to-FMOD import pipeline row by row:
  resolve audio → pre-check bus/bank → import audio → create event
  → add track → add sound → assign bus → assign bank → log result

Rules:
- If event_path already exists: skip row + warning
- If bus/bank not found: skip row + warning (no event created)
- If TCP connection fails: abort entire batch
- Any other row error: log failure, continue to next row
"""

import json
import os
from dataclasses import dataclass, field
from typing import Optional

from fmod_batch_import.csv_parser import CSVReader, CSVParseError
from fmod_batch_import.audio_resolver import AudioResolver
from fmod_batch_import.path_normalizer import PathNormalizer
from fmod_batch_import.log_writer import LogWriter
from fmod_batch_import.fmod_client import FMODClient
from fmod_batch_import.js_builder import (
    js_lookup,
    js_create_event,
    js_add_group_track,
    js_add_sound,
    js_import_audio,
    js_assign_bus,
    js_assign_bank,
    js_save,
)
from fmod_batch_import.bus_bank_manager import lookup_bus, lookup_bank


class FMODConnectionError(Exception):
    """Raised when FMOD TCP connection is lost or unavailable."""


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
    rows: list = field(default_factory=list)


class Orchestrator:
    """
    Drives the full CSV-to-FMOD import pipeline.

    Args:
        csv_path: Path to the CSV file.
        audio_dir: Directory to search for audio files.
        fmod_client: Connected FMODClient instance.
        log_writer: Optional LogWriter; if None, one is created next to CSV.
    """

    def __init__(
        self,
        csv_path: str,
        audio_dir: str,
        fmod_client: FMODClient,
        log_writer: Optional[LogWriter] = None,
    ):
        self.csv_path = csv_path
        self.audio_dir = audio_dir
        self.client = fmod_client
        self.csv_dir = os.path.dirname(os.path.abspath(csv_path))
        self.log_writer = log_writer or LogWriter(
            output_dir=self.csv_dir,
            csv_filename=os.path.basename(csv_path),
        )
        self._csv_reader = CSVReader()
        self._audio_resolver = AudioResolver(audio_dir)
        self._path_normalizer = PathNormalizer()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> BatchSummary:
        """Execute the full batch import. Returns a BatchSummary."""
        summary = BatchSummary()

        # Parse CSV
        try:
            rows = self._csv_reader.read_file(self.csv_path)
        except (CSVParseError, FileNotFoundError) as exc:
            raise ValueError(f"CSV error: {exc}") from exc

        summary.total = len(rows)

        for csv_row in rows:
            result = self._process_row(csv_row)
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

        # Save project after all rows
        try:
            self._exec(js_save())
        except FMODConnectionError:
            pass  # Already handled per-row; save is best-effort

        self.log_writer.write()
        return summary

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _exec(self, js: str) -> dict:
        """
        Execute JS via FMODClient and parse JSON response.
        Raises FMODConnectionError on connection failure.
        """
        response = self.client.execute(js)
        if response is None:
            raise FMODConnectionError("FMOD TCP connection lost")
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            return {"ok": False, "error": f"Non-JSON response: {response[:200]}"}

    def _process_row(self, csv_row) -> RowResult:
        """Process a single CSV row. Returns RowResult."""
        idx = csv_row.row_index
        event_path = csv_row.event_path.strip()
        audio_name = csv_row.audio_path.strip()
        asset_folder = csv_row.asset_path.strip()
        bus_path = csv_row.bus_path.strip()
        bank_name = csv_row.bank_name.strip()

        # Normalize paths
        try:
            norm = self._path_normalizer.normalize_row(
                audio_path=audio_name,
                event_path=event_path,
                asset_path=asset_folder,
                bus_path=bus_path,
                bank_name=bank_name,
                row_index=idx,
            )
            event_path = norm.event_path
            bus_path = norm.bus_path
            bank_name = norm.bank_name
        except Exception as exc:
            return RowResult(idx, "fail", event_path, audio_name, f"Path error: {exc}")

        # --- Step 1: Check if event already exists ---
        try:
            lookup_result = self._exec(js_lookup(event_path))
            if lookup_result.get("ok"):
                return RowResult(idx, "skip", event_path, audio_name,
                                 f"Event already exists: {event_path}")
        except FMODConnectionError as exc:
            raise  # Propagate to abort batch

        # --- Step 2: Pre-check bus/bank ---
        bus_id = None
        bank_id = None

        if bus_path:
            try:
                bus_result = self._exec(lookup_bus(bus_path))
                if not bus_result.get("ok"):
                    return RowResult(idx, "skip", event_path, audio_name,
                                     f"Bus not found: {bus_path}")
                bus_id = bus_result.get("bus_id")
            except FMODConnectionError:
                raise

        if bank_name:
            try:
                bank_result = self._exec(lookup_bank(bank_name))
                if not bank_result.get("ok"):
                    return RowResult(idx, "skip", event_path, audio_name,
                                     f"Bank not found: {bank_name}")
                bank_id = bank_result.get("bank_id")
            except FMODConnectionError:
                raise

        # --- Step 3: Resolve audio file ---
        try:
            audio_abs = self._audio_resolver.resolve(audio_name)
        except FileNotFoundError as exc:
            return RowResult(idx, "fail", event_path, audio_name, str(exc))

        # --- Step 4: Import audio asset ---
        try:
            import_result = self._exec(js_import_audio(str(audio_abs)))
            if not import_result.get("ok"):
                return RowResult(idx, "fail", event_path, audio_name,
                                 f"Audio import failed: {import_result.get('error')}")
            asset_id = import_result.get("asset_id")
        except FMODConnectionError:
            raise

        # --- Step 5: Create event ---
        try:
            create_result = self._exec(js_create_event(event_path))
            if not create_result.get("ok"):
                return RowResult(idx, "fail", event_path, audio_name,
                                 f"Event create failed: {create_result.get('error')}")
            event_id = create_result.get("id")
        except FMODConnectionError:
            raise

        # --- Step 6: Add group track ---
        try:
            track_result = self._exec(js_add_group_track(event_id, "Audio"))
            if not track_result.get("ok"):
                return RowResult(idx, "fail", event_path, audio_name,
                                 f"Track add failed: {track_result.get('error')}")
            track_id = track_result.get("track_id")
        except FMODConnectionError:
            raise

        # --- Step 7: Add sound ---
        try:
            sound_result = self._exec(js_add_sound(track_id, asset_id))
            if not sound_result.get("ok"):
                return RowResult(idx, "fail", event_path, audio_name,
                                 f"Sound add failed: {sound_result.get('error')}")
        except FMODConnectionError:
            raise

        # --- Step 8: Assign bus ---
        if bus_id:
            try:
                bus_assign = self._exec(js_assign_bus(event_id, bus_id))
                if not bus_assign.get("ok"):
                    self.log_writer.add_warning(
                        f"Row {idx}: Bus assign failed: {bus_assign.get('error')}")
            except FMODConnectionError:
                raise

        # --- Step 9: Assign bank ---
        if bank_id:
            try:
                bank_assign = self._exec(js_assign_bank(event_id, bank_id))
                if not bank_assign.get("ok"):
                    self.log_writer.add_warning(
                        f"Row {idx}: Bank assign failed: {bank_assign.get('error')}")
            except FMODConnectionError:
                raise

        return RowResult(idx, "success", event_path, audio_name, "OK")
