"""Log writer module for generating Markdown log files."""

from datetime import datetime
from pathlib import Path
from typing import Optional


class LogWriter:
    """Writes Markdown log files for batch import operations."""

    def __init__(self, output_dir: Path, csv_filename: str):
        """Initialize the log writer.
        
        Args:
            output_dir: Directory where log files will be written
            csv_filename: Name of the CSV file being processed
        """
        self.output_dir = Path(output_dir)
        self.csv_filename = csv_filename
        self.timestamp = datetime.now()
        
        # Initialize counters
        self.success_count = 0
        self.skip_count = 0
        self.fail_count = 0
        self.total_count = 0
        
        # Storage for row results and warnings
        self.rows: list[dict] = []
        self.warnings: list[str] = []
        
        # Generate timestamped filename
        self.log_filename = self._generate_filename()
        self.log_path = self.output_dir / self.log_filename

    def _generate_filename(self) -> str:
        """Generate a timestamped filename to avoid overwrites."""
        timestamp_str = self.timestamp.strftime("%Y%m%d_%H%M%S")
        base_name = Path(self.csv_filename).stem
        return f"{base_name}_{timestamp_str}_log.md"

    def log_row(
        self,
        row_num: int,
        audio_file: str,
        event_path: str,
        status: str,
        message: str = "",
        defaults_applied: str = "",
        inheritance_source: str = "",
        template_used: str = ""
    ) -> None:
        """Log the result of processing a single row.
        
        Args:
            row_num: Row number in the CSV file
            audio_file: Path to the audio file
            event_path: FMOD event path
            status: One of 'success', 'skip', 'fail'
            message: Optional message (e.g., error details)
            defaults_applied: Comma-separated list of default values applied
            inheritance_source: Source of inherited values (e.g., parent event)
            template_used: Name of template used for this row
        """
        self.rows.append({
            "row": row_num,
            "audio": audio_file,
            "event": event_path,
            "status": status,
            "message": message,
            "defaults_applied": defaults_applied,
            "inheritance_source": inheritance_source,
            "template_used": template_used
        })
        
        self.total_count += 1
        if status == "success":
            self.success_count += 1
        elif status == "skip":
            self.skip_count += 1
        elif status == "fail":
            self.fail_count += 1

    def add_warning(self, warning: str) -> None:
        """Add a warning message to the log."""
        self.warnings.append(warning)

    def _generate_header(self) -> str:
        """Generate the markdown header section."""
        lines = [
            "# FMOD Batch Import Log",
            "",
            f"**CSV File:** `{self.csv_filename}`",
            f"**Timestamp:** {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ]
        return "\n".join(lines)

    def _generate_table(self) -> str:
        """Generate the results table section."""
        if not self.rows:
            return "## Results\n\nNo rows processed.\n"
        
        lines = [
            "## Results",
            "",
            "| Row | Audio | Event | Status | Message | Defaults Applied | Inheritance Source | Template Used |",
            "|-----|-------|-------|--------|---------|------------------|-------------------|---------------|"
        ]
        
        for row in self.rows:
            # Escape pipe characters in messages and other fields
            message = row["message"].replace("|", "\\|")
            defaults = str(row.get("defaults_applied", "")).replace("|", "\\|")
            inheritance = str(row.get("inheritance_source", "")).replace("|", "\\|")
            template = str(row.get("template_used", "")).replace("|", "\\|")
            lines.append(
                f"| {row['row']} | `{row['audio']}` | `{row['event']}` | "
                f"{row['status']} | {message} | {defaults} | {inheritance} | {template} |"
            )
        
        lines.append("")
        return "\n".join(lines)

    def _generate_warnings(self) -> str:
        """Generate the warnings section."""
        if not self.warnings:
            return ""
        
        lines = ["## Warnings", ""]
        for warning in self.warnings:
            lines.append(f"- ⚠️ {warning}")
        lines.append("")
        return "\n".join(lines)

    def _generate_summary(self) -> str:
        """Generate the summary section."""
        lines = [
            "## Summary",
            "",
            f"- **Total:** {self.total_count}",
            f"- ✅ **Success:** {self.success_count}",
            f"- ⏭️ **Skip:** {self.skip_count}",
            f"- ❌ **Fail:** {self.fail_count}",
            ""
        ]
        return "\n".join(lines)

    def generate_markdown(self) -> str:
        """Generate the complete markdown content."""
        sections = [
            self._generate_header(),
            self._generate_table(),
            self._generate_warnings(),
            self._generate_summary()
        ]
        return "\n".join(sections)

    def write(self) -> Path:
        """Write the log file to disk.
        
        Returns:
            Path to the written log file
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        content = self.generate_markdown()
        self.log_path.write_text(content, encoding="utf-8")
        return self.log_path

    def get_summary(self) -> dict:
        """Get the summary counts.
        
        Returns:
            Dictionary with success, skip, fail, and total counts
        """
        return {
            "success": self.success_count,
            "skip": self.skip_count,
            "fail": self.fail_count,
            "total": self.total_count
        }
