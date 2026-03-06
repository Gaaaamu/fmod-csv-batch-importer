"""Tests for Orchestrator — mocks FMODClient to avoid real FMOD connection.

Batch architecture: Python preprocessing + ONE batch JS call + ONE save call.
Mock responses follow the new sequence:
  1. Single batch call  → {ok: true, results: [...]}
  2. save              → "ok"
"""

import json
import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from fmod_batch_import.orchestrator import Orchestrator
from fmod_batch_import.fmod_client import FMODConnectionError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_csv(rows: list[dict], tmp_dir: str) -> str:
    """Write a CSV file with the 5 required columns."""
    path = os.path.join(tmp_dir, "test_import.csv")
    with open(path, "w", encoding="utf-8") as f:
        f.write("audio_path,event_path,asset_path,bus_path,bank_name\n")
        for r in rows:
            f.write(
                f"{r.get('audio_path','')},{r.get('event_path','')},{r.get('asset_path','')},"
                f"{r.get('bus_path','')},{r.get('bank_name','')}\n"
            )
    return path


def _make_audio(tmp_dir: str, name: str = "test_audio.wav") -> str:
    """Create a dummy audio file."""
    path = os.path.join(tmp_dir, name)
    Path(path).write_bytes(b"RIFF")
    return path


def _mock_client(responses: list) -> MagicMock:
    """Build a mock FMODClient whose execute() returns responses in sequence."""
    client = MagicMock()
    client.execute.side_effect = [json.dumps(r) for r in responses]
    return client


def _batch_ok(results: list[dict]) -> dict:
    """Shorthand for a successful batch call response."""
    return {"ok": True, "results": results}


def _row_result(
    row_index: int,
    status: str,
    event_path: str,
    audio_name: str,
    message: str = "OK",
    warnings: list[str] | None = None,
) -> dict:
    """Shorthand for a single per-row result dict from JS."""
    return {
        "row_index": row_index,
        "status": status,
        "event_path": event_path,
        "audio_name": audio_name,
        "message": message,
        "warnings": warnings or [],
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestOrchestratorSuccess:
    def test_single_row_success(self, tmp_path):
        """A valid row with no bus/bank should succeed."""
        audio_dir = str(tmp_path)
        _make_audio(audio_dir, "hero_01.wav")
        csv_path = _make_csv([{
            "audio_path": "hero_01.wav",
            "event_path": "event:/VO/hero_01",
        }], audio_dir)

        client = _mock_client([
            _batch_ok([
                _row_result(1, "success", "event:/VO/hero_01", "hero_01.wav"),
            ]),
            "ok",  # save
        ])

        orch = Orchestrator(csv_path, audio_dir, client)
        summary = orch.run()

        assert summary.success == 1
        assert summary.fail == 0
        assert summary.skip == 0
        assert summary.total == 1

    def test_event_already_exists_skips(self, tmp_path):
        """If JS reports event already exists, row should be skipped."""
        audio_dir = str(tmp_path)
        _make_audio(audio_dir, "hero_01.wav")
        csv_path = _make_csv([{
            "audio_path": "hero_01.wav",
            "event_path": "event:/VO/hero_01",
        }], audio_dir)

        client = _mock_client([
            _batch_ok([
                _row_result(1, "skip", "event:/VO/hero_01", "hero_01.wav",
                            message="Event already exists: event:/VO/hero_01"),
            ]),
            "ok",  # save
        ])

        orch = Orchestrator(csv_path, audio_dir, client)
        summary = orch.run()

        assert summary.skip == 1
        assert summary.success == 0
        assert summary.fail == 0

    def test_bus_not_found_warns_and_continues(self, tmp_path):
        """JS reports bus not found as a warning; row still succeeds."""
        audio_dir = str(tmp_path)
        _make_audio(audio_dir, "hero_01.wav")
        csv_path = _make_csv([{
            "audio_path": "hero_01.wav",
            "event_path": "event:/VO/hero_01",
            "bus_path": "bus:/SFX",
        }], audio_dir)

        client = _mock_client([
            _batch_ok([
                _row_result(1, "success", "event:/VO/hero_01", "hero_01.wav",
                            warnings=["Bus not found: bus:/SFX"]),
            ]),
            "ok",  # save
        ])

        orch = Orchestrator(csv_path, audio_dir, client)
        summary = orch.run()

        assert summary.success == 1
        assert summary.skip == 0
        assert summary.fail == 0

    def test_bank_not_found_warns_and_continues(self, tmp_path):
        """JS reports bank not found as a warning; row still succeeds."""
        audio_dir = str(tmp_path)
        _make_audio(audio_dir, "hero_01.wav")
        csv_path = _make_csv([{
            "audio_path": "hero_01.wav",
            "event_path": "event:/VO/hero_01",
            "bank_name": "bank:/Master",
        }], audio_dir)

        client = _mock_client([
            _batch_ok([
                _row_result(1, "success", "event:/VO/hero_01", "hero_01.wav",
                            warnings=["Bank not found: bank:/Master"]),
            ]),
            "ok",  # save
        ])

        orch = Orchestrator(csv_path, audio_dir, client)
        summary = orch.run()

        assert summary.success == 1
        assert summary.skip == 0
        assert summary.fail == 0

    def test_audio_not_found_fails_row(self, tmp_path):
        """Missing audio file (Python resolve fails) → row marked fail, no batch call."""
        audio_dir = str(tmp_path)
        # No audio file created
        csv_path = _make_csv([{
            "audio_path": "missing.wav",
            "event_path": "event:/VO/missing",
        }], audio_dir)

        # No batch call since prepped_rows is empty; only save is called.
        client = _mock_client([
            "ok",  # save
        ])

        orch = Orchestrator(csv_path, audio_dir, client)
        summary = orch.run()

        assert summary.fail == 1
        assert summary.success == 0

    def test_row_failure_does_not_stop_batch(self, tmp_path):
        """A Python-side failing row (audio missing) does not prevent other rows."""
        audio_dir = str(tmp_path)
        _make_audio(audio_dir, "good.wav")
        csv_path = _make_csv([
            {"audio_path": "missing.wav", "event_path": "event:/VO/missing"},
            {"audio_path": "good.wav",    "event_path": "event:/VO/good"},
        ], audio_dir)

        # Row 1 fails Python-side (audio missing) → only row 2 goes into batch
        client = _mock_client([
            _batch_ok([
                _row_result(2, "success", "event:/VO/good", "good.wav"),
            ]),
            "ok",  # save
        ])

        orch = Orchestrator(csv_path, audio_dir, client)
        summary = orch.run()

        assert summary.fail == 1
        assert summary.success == 1
        assert summary.total == 2

    def test_tcp_failure_aborts_batch(self, tmp_path):
        """TCP connection failure on the batch call aborts the entire batch."""
        audio_dir = str(tmp_path)
        _make_audio(audio_dir, "hero.wav")
        csv_path = _make_csv([
            {"audio_path": "hero.wav", "event_path": "event:/VO/hero"},
        ], audio_dir)

        client = MagicMock()
        client.execute.side_effect = FMODConnectionError("FMOD connection lost")

        orch = Orchestrator(csv_path, audio_dir, client)
        with pytest.raises(FMODConnectionError):
            orch.run()

    def test_multiple_rows_single_batch_call(self, tmp_path):
        """Multiple rows go through ONE batch call, not separate calls per row."""
        audio_dir = str(tmp_path)
        for name in ["a.wav", "b.wav", "c.wav"]:
            _make_audio(audio_dir, name)
        csv_path = _make_csv([
            {"audio_path": "a.wav", "event_path": "event:/A"},
            {"audio_path": "b.wav", "event_path": "event:/B"},
            {"audio_path": "c.wav", "event_path": "event:/C"},
        ], audio_dir)

        client = _mock_client([
            _batch_ok([
                _row_result(1, "success", "event:/A", "a.wav"),
                _row_result(2, "success", "event:/B", "b.wav"),
                _row_result(3, "success", "event:/C", "c.wav"),
            ]),
            "ok",  # save
        ])

        orch = Orchestrator(csv_path, audio_dir, client)
        summary = orch.run()

        assert summary.success == 3
        assert summary.total == 3
        # Exactly 2 TCP calls: 1 batch + 1 save
        assert client.execute.call_count == 2

    def test_js_fail_result_counts_as_fail(self, tmp_path):
        """JS-side failure in a row (e.g. addEvent null) is counted as fail."""
        audio_dir = str(tmp_path)
        _make_audio(audio_dir, "hero.wav")
        csv_path = _make_csv([{
            "audio_path": "hero.wav",
            "event_path": "event:/VO/hero",
        }], audio_dir)

        client = _mock_client([
            _batch_ok([
                _row_result(1, "fail", "event:/VO/hero", "hero.wav",
                            message="addEvent null"),
            ]),
            "ok",  # save
        ])

        orch = Orchestrator(csv_path, audio_dir, client)
        summary = orch.run()

        assert summary.fail == 1
        assert summary.success == 0

    def test_result_order_preserved(self, tmp_path):
        """Results appear in original CSV row order even if JS returns them in order."""
        audio_dir = str(tmp_path)
        for name in ["x.wav", "y.wav"]:
            _make_audio(audio_dir, name)
        csv_path = _make_csv([
            {"audio_path": "x.wav", "event_path": "event:/X"},
            {"audio_path": "y.wav", "event_path": "event:/Y"},
        ], audio_dir)

        client = _mock_client([
            _batch_ok([
                _row_result(1, "success", "event:/X", "x.wav"),
                _row_result(2, "skip",    "event:/Y", "y.wav",
                            message="Event already exists: event:/Y"),
            ]),
            "ok",  # save
        ])

        orch = Orchestrator(csv_path, audio_dir, client)
        summary = orch.run()

        assert summary.success == 1
        assert summary.skip == 1
        assert summary.rows[0].row_index == 1
        assert summary.rows[1].row_index == 2
