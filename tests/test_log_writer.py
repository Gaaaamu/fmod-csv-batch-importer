"""Tests for the log_writer module."""

import re
from datetime import datetime
from pathlib import Path

import pytest

from fmod_batch_import.log_writer import LogWriter


class TestLogWriter:
    """Test suite for LogWriter class."""

    def test_log_file_written_to_correct_directory(self, tmp_path):
        """Test that log file is written to the specified directory."""
        output_dir = tmp_path / "logs"
        csv_filename = "test_data.csv"
        
        writer = LogWriter(output_dir, csv_filename)
        writer.log_row(1, "audio.wav", "/event/path", "success")
        log_path = writer.write()
        
        assert log_path.parent == output_dir
        assert log_path.exists()

    def test_summary_counts_accurate(self, tmp_path):
        """Test that summary counts are accurate after logging rows."""
        writer = LogWriter(tmp_path, "test.csv")
        
        # Log various statuses
        writer.log_row(1, "a.wav", "/event/1", "success")
        writer.log_row(2, "b.wav", "/event/2", "success")
        writer.log_row(3, "c.wav", "/event/3", "skip")
        writer.log_row(4, "d.wav", "/event/4", "fail")
        writer.log_row(5, "e.wav", "/event/5", "fail")
        
        summary = writer.get_summary()
        
        assert summary["success"] == 2
        assert summary["skip"] == 1
        assert summary["fail"] == 2
        assert summary["total"] == 5

    def test_timestamped_filename_generation(self, tmp_path):
        """Test that filename includes timestamp to avoid overwrites."""
        csv_filename = "my_data.csv"
        writer = LogWriter(tmp_path, csv_filename)
        
        # Filename should contain timestamp pattern and base name
        assert writer.log_filename.startswith("my_data_")
        assert writer.log_filename.endswith("_log.md")
        
        # Extract timestamp portion
        timestamp_match = re.search(r"my_data_(\d{8}_\d{6})_log\.md", writer.log_filename)
        assert timestamp_match is not None
        
        # Verify timestamp format (YYYYMMDD_HHMMSS)
        timestamp_str = timestamp_match.group(1)
        assert len(timestamp_str) == 15  # YYYYMMDD_HHMMSS
        assert timestamp_str[8] == "_"

    def test_markdown_header_format(self, tmp_path):
        """Test that markdown header is properly formatted."""
        writer = LogWriter(tmp_path, "test.csv")
        markdown = writer.generate_markdown()
        
        assert "# FMOD Batch Import Log" in markdown
        assert "**CSV File:** `test.csv`" in markdown
        assert "**Timestamp:**" in markdown

    def test_markdown_table_format(self, tmp_path):
        """Test that results table is properly formatted."""
        writer = LogWriter(tmp_path, "test.csv")
        writer.log_row(1, "audio.wav", "/events/test", "success", "Created successfully")
        
        markdown = writer.generate_markdown()
        
        # Check table headers
        assert "| Row | Audio | Event | Status | Message |" in markdown
        assert "|-----|-------|-------|--------|---------|" in markdown
        
        # Check row data
        assert "| 1 | `audio.wav` | `/events/test` | success | Created successfully |" in markdown

    def test_markdown_warnings_section(self, tmp_path):
        """Test that warnings section is included when warnings exist."""
        writer = LogWriter(tmp_path, "test.csv")
        writer.add_warning("File not found: missing.wav")
        writer.add_warning("Invalid format")
        
        markdown = writer.generate_markdown()
        
        assert "## Warnings" in markdown
        assert "- ⚠️ File not found: missing.wav" in markdown
        assert "- ⚠️ Invalid format" in markdown

    def test_markdown_no_warnings_section_when_empty(self, tmp_path):
        """Test that warnings section is omitted when no warnings."""
        writer = LogWriter(tmp_path, "test.csv")
        markdown = writer.generate_markdown()
        
        assert "## Warnings" not in markdown

    def test_markdown_summary_section(self, tmp_path):
        """Test that summary section is properly formatted."""
        writer = LogWriter(tmp_path, "test.csv")
        writer.log_row(1, "a.wav", "/event/1", "success")
        writer.log_row(2, "b.wav", "/event/2", "fail")
        
        markdown = writer.generate_markdown()
        
        assert "## Summary" in markdown
        assert "**Total:** 2" in markdown
        assert "**Success:** 1" in markdown
        assert "**Fail:** 1" in markdown

    def test_log_row_without_message(self, tmp_path):
        """Test logging a row without an optional message."""
        writer = LogWriter(tmp_path, "test.csv")
        writer.log_row(1, "audio.wav", "/events/test", "success")
        
        assert len(writer.rows) == 1
        assert writer.rows[0]["message"] == ""

    def test_multiple_logs_different_timestamps(self, tmp_path):
        """Test that multiple log files have different timestamps."""
        writer1 = LogWriter(tmp_path, "test.csv")
        import time
        time.sleep(1.1)  # Wait >1 second to ensure different timestamp
        writer2 = LogWriter(tmp_path, "test.csv")
        
        assert writer1.log_filename != writer2.log_filename

    def test_empty_rows_table_message(self, tmp_path):
        """Test that empty rows show appropriate message."""
        writer = LogWriter(tmp_path, "test.csv")
        markdown = writer.generate_markdown()
        
        assert "No rows processed." in markdown

    def test_pipe_character_escaping(self, tmp_path):
        """Test that pipe characters in messages are properly escaped."""
        writer = LogWriter(tmp_path, "test.csv")
        writer.log_row(1, "audio.wav", "/events/test", "fail", "Error: A | B")
        
        markdown = writer.generate_markdown()
        
        # Pipe should be escaped
        assert "Error: A \\| B" in markdown


class TestLogWriterIntegration:
    """Integration tests for LogWriter."""

    def test_full_workflow(self, tmp_path):
        """Test complete workflow from initialization to file output."""
        output_dir = tmp_path / "output"
        csv_file = "batch_import.csv"
        
        # Create writer and log some operations
        writer = LogWriter(output_dir, csv_file)
        
        writer.log_row(1, "sfx/impact.wav", "/sfx/impact", "success")
        writer.log_row(2, "sfx/jump.wav", "/sfx/jump", "success")
        writer.log_row(3, "music/theme.wav", "/music/theme", "skip")
        writer.log_row(4, "sfx/explosion.wav", "/sfx/explosion", "fail", "File not found")
        writer.add_warning("Low disk space")
        
        # Write the log
        log_path = writer.write()
        
        # Verify file was created
        assert log_path.exists()
        
        # Read and verify content
        content = log_path.read_text(encoding="utf-8")
        
        # Header checks
        assert "# FMOD Batch Import Log" in content
        assert "batch_import.csv" in content
        
        # Table checks
        assert "sfx/impact.wav" in content
        assert "/sfx/jump" in content
        assert "File not found" in content
        
        # Warnings
        assert "Low disk space" in content
        
        # Summary
        assert "**Total:** 4" in content
        assert "**Success:** 2" in content
        assert "**Skip:** 1" in content
        assert "**Fail:** 1" in content

    def test_directory_created_if_not_exists(self, tmp_path):
        """Test that output directory is created if it doesn't exist."""
        deep_dir = tmp_path / "level1" / "level2" / "logs"
        writer = LogWriter(deep_dir, "test.csv")
        writer.log_row(1, "a.wav", "/event", "success")
        
        assert not deep_dir.exists()
        writer.write()
        assert deep_dir.exists()
