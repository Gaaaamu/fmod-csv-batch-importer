"""Tests for Orchestrator — mocks FMODClient to avoid real FMOD connection."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from fmod_batch_import.orchestrator import Orchestrator, FMODConnectionError


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
    """Build a mock FMODClient that returns responses in sequence."""
    client = MagicMock()
    client.execute.side_effect = [json.dumps(r) for r in responses]
    return client


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
            {"ok": False, "id": None, "error": "Not found"},   # lookup event (not exists)
            {"ok": True, "asset_id": "asset-guid-1"},           # import audio
            {"ok": True, "id": "event-guid-1"},                 # create event
            {"ok": True, "track_id": "track-guid-1"},           # add track
            {"ok": True, "sound_id": "sound-guid-1"},           # add sound
            "ok",                                               # save
        ])

        orch = Orchestrator(csv_path, audio_dir, client)
        summary = orch.run()

        assert summary.success == 1
        assert summary.fail == 0
        assert summary.skip == 0
        assert summary.total == 1

    def test_event_already_exists_skips(self, tmp_path):
        """If event already exists, row should be skipped."""
        audio_dir = str(tmp_path)
        _make_audio(audio_dir, "hero_01.wav")
        csv_path = _make_csv([{
            "audio_path": "hero_01.wav",
            "event_path": "event:/VO/hero_01",
        }], audio_dir)

        client = _mock_client([
            {"ok": True, "id": "existing-guid"},  # lookup event (exists!)
            "ok",                                  # save
        ])

        orch = Orchestrator(csv_path, audio_dir, client)
        summary = orch.run()

        assert summary.skip == 1
        assert summary.success == 0
        assert summary.fail == 0

    def test_bus_not_found_skips(self, tmp_path):
        """If bus not found, row should be skipped."""
        audio_dir = str(tmp_path)
        _make_audio(audio_dir, "hero_01.wav")
        csv_path = _make_csv([{
            "audio_path": "hero_01.wav",
            "event_path": "event:/VO/hero_01",
            "bus_path": "bus:/SFX",
        }], audio_dir)

        client = _mock_client([
            {"ok": False, "id": None, "error": "Not found"},   # lookup event
            {"ok": False, "bus_id": None, "error": "Bus not found"},  # lookup bus
            "ok",                                               # save
        ])

        orch = Orchestrator(csv_path, audio_dir, client)
        summary = orch.run()

        assert summary.skip == 1
        assert summary.success == 0

    def test_bank_not_found_skips(self, tmp_path):
        """If bank not found, row should be skipped."""
        audio_dir = str(tmp_path)
        _make_audio(audio_dir, "hero_01.wav")
        csv_path = _make_csv([{
            "audio_path": "hero_01.wav",
            "event_path": "event:/VO/hero_01",
            "bank_name": "bank:/Master",
        }], audio_dir)

        client = _mock_client([
            {"ok": False, "id": None, "error": "Not found"},    # lookup event
            {"ok": False, "bank_id": None, "error": "Not found"},  # lookup bank
            "ok",                                                # save
        ])

        orch = Orchestrator(csv_path, audio_dir, client)
        summary = orch.run()

        assert summary.skip == 1

    def test_audio_not_found_fails_row(self, tmp_path):
        """Missing audio file should fail the row but continue batch."""
        audio_dir = str(tmp_path)
        # No audio file created
        csv_path = _make_csv([{
            "audio_path": "missing.wav",
            "event_path": "event:/VO/missing",
        }], audio_dir)

        client = _mock_client([
            {"ok": False, "id": None, "error": "Not found"},  # lookup event
            "ok",                                              # save
        ])

        orch = Orchestrator(csv_path, audio_dir, client)
        summary = orch.run()

        assert summary.fail == 1
        assert summary.success == 0

    def test_row_failure_does_not_stop_batch(self, tmp_path):
        """A failing row should not stop subsequent rows."""
        audio_dir = str(tmp_path)
        _make_audio(audio_dir, "good.wav")
        csv_path = _make_csv([
            {"audio_path": "missing.wav", "event_path": "event:/VO/missing"},
            {"audio_path": "good.wav", "event_path": "event:/VO/good"},
        ], audio_dir)

        client = _mock_client([
            {"ok": False, "id": None, "error": "Not found"},  # lookup event row1
            # row1 fails (audio not found) — no more calls for row1
            {"ok": False, "id": None, "error": "Not found"},  # lookup event row2
            {"ok": True, "asset_id": "asset-2"},               # import audio row2
            {"ok": True, "id": "event-2"},                     # create event row2
            {"ok": True, "track_id": "track-2"},               # add track row2
            {"ok": True, "sound_id": "sound-2"},               # add sound row2
            "ok",                                              # save
        ])

        orch = Orchestrator(csv_path, audio_dir, client)
        summary = orch.run()

        assert summary.fail == 1
        assert summary.success == 1
        assert summary.total == 2

    def test_tcp_failure_aborts_batch(self, tmp_path):
        """TCP connection failure should abort the entire batch."""
        audio_dir = str(tmp_path)
        _make_audio(audio_dir, "hero.wav")
        csv_path = _make_csv([
            {"audio_path": "hero.wav", "event_path": "event:/VO/hero"},
        ], audio_dir)

        client = MagicMock()
        client.execute.return_value = None  # Simulate connection lost

        orch = Orchestrator(csv_path, audio_dir, client)
        with pytest.raises(FMODConnectionError):
            orch.run()
