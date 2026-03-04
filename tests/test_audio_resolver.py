"""Tests for AudioResolver strict matching."""

from pathlib import Path

import pytest

from fmod_batch_import.audio_resolver import AudioResolver


def _write_audio(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("audio", encoding="utf-8")


def test_extensionless_resolution(tmp_path: Path) -> None:
    audio_dir = tmp_path / "audio"
    _write_audio(audio_dir / "audio01.wav")

    resolver = AudioResolver(audio_dir)

    resolved = resolver.resolve("audio01")

    assert resolved == (audio_dir / "audio01.wav").resolve()


def test_duplicate_resolution_warns_and_picks_first(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    audio_dir = tmp_path / "audio"
    _write_audio(audio_dir / "a" / "dup.wav")
    _write_audio(audio_dir / "b" / "dup.wav")

    resolver = AudioResolver(audio_dir)

    with caplog.at_level("WARNING"):
        resolved = resolver.resolve("dup.wav")

    assert resolved == (audio_dir / "a" / "dup.wav").resolve()
    assert "Multiple audio files matched 'dup.wav'" in caplog.text


def test_case_sensitive_matching(tmp_path: Path) -> None:
    audio_dir = tmp_path / "audio"
    _write_audio(audio_dir / "Case.wav")

    resolver = AudioResolver(audio_dir)

    with pytest.raises(FileNotFoundError):
        resolver.resolve("case.wav")


def test_recursive_search(tmp_path: Path) -> None:
    audio_dir = tmp_path / "audio"
    _write_audio(audio_dir / "nested" / "deep" / "sound.ogg")

    resolver = AudioResolver(audio_dir)

    resolved = resolver.resolve("sound.ogg")

    assert resolved == (audio_dir / "nested" / "deep" / "sound.ogg").resolve()


def test_file_not_found(tmp_path: Path) -> None:
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    resolver = AudioResolver(audio_dir)

    with pytest.raises(FileNotFoundError):
        resolver.resolve("missing.wav")
