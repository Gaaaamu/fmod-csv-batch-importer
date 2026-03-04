"""
CSV Parser module for FMOD Batch Import.

Handles reading and validation of CSV files with strict schema enforcement.
"""
import csv
from collections import namedtuple
from typing import List, TextIO, Optional


# Expected column names for the CSV schema
EXPECTED_COLUMNS = ["audio_path", "event_path", "asset_path", "bus_path", "bank_name"]

# Named tuple representing a parsed CSV row
CSVRow = namedtuple("CSVRow", ["row_index", "audio_path", "event_path", "asset_path", "bus_path", "bank_name"])


class CSVParseError(Exception):
    """Exception raised for CSV parsing errors."""
    
    def __init__(self, message: str, row_number: Optional[int] = None):
        self.message = message
        self.row_number = row_number
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        if self.row_number is not None:
            return f"CSV Error at row {self.row_number}: {self.message}"
        return f"CSV Error: {self.message}"


class CSVReader:
    """
    Reads and validates CSV files with strict schema enforcement.
    
    Expects exactly 5 columns:
    - audio_path
    - event_path
    - asset_path
    - bus_path
    - bank_name
    
    Handles:
    - UTF-8 BOM removal
    - Empty line skipping
    - Strict column count validation (no extra columns allowed)
    """
    
    def __init__(self, expected_columns: Optional[List[str]] = None):
        """
        Initialize CSVReader.
        
        Args:
            expected_columns: List of expected column names. Defaults to EXPECTED_COLUMNS.
        """
        self.expected_columns = expected_columns or EXPECTED_COLUMNS
    
    def read(self, file_obj: TextIO) -> List[CSVRow]:
        """
        Read and parse CSV from file object.
        
        Args:
            file_obj: File-like object to read from.
            
        Returns:
            List of CSVRow namedtuples.
            
        Raises:
            CSVParseError: If CSV is invalid or malformed.
        """
        # Read raw content to handle BOM
        raw_content = file_obj.read()
        
        # Handle empty file
        if not raw_content or not raw_content.strip():
            raise CSVParseError("File is empty")
        
        # Remove UTF-8 BOM if present
        raw_content = raw_content.lstrip('\ufeff')
        raw_content = raw_content.lstrip('\ufeff')
        if raw_content.startswith('\ufeff'):
            raw_content = raw_content[1:]
        
        # Parse CSV
        lines = raw_content.splitlines()
        if not lines:
            raise CSVParseError("File has no content")
        
        # Read header
        header_line = lines[0].strip()
        if not header_line:
            raise CSVParseError("Missing header row")
        
        header_reader = csv.reader([header_line])
        header = next(header_reader)
        
        # Validate header columns
        if len(header) != len(self.expected_columns):
            raise CSVParseError(
                f"Header has {len(header)} columns, expected {len(self.expected_columns)}",
                row_number=1
            )
        
        if header != self.expected_columns:
            raise CSVParseError(
                f"Invalid header. Expected: {self.expected_columns}, Got: {header}",
                row_number=1
            )
        
        # Parse data rows
        rows = []
        row_index = 0
        
        for line_num, line in enumerate(lines[1:], start=2):
            stripped = line.strip()
            
            # Skip empty lines
            if not stripped:
                continue
            
            # Parse the row
            row_reader = csv.reader([stripped])
            try:
                fields = next(row_reader)
            except csv.Error as e:
                raise CSVParseError(f"CSV parse error: {e}", row_number=line_num)
            
            # Validate column count
            if len(fields) != len(self.expected_columns):
                raise CSVParseError(
                    f"Row has {len(fields)} columns, expected {len(self.expected_columns)}",
                    row_number=line_num
                )
            
            # Normalize empty strings (None -> "")
            normalized_fields = [field if field is not None else "" for field in fields]
            
            # Create CSVRow
            row_index += 1
            row = CSVRow(
                row_index=row_index,
                audio_path=normalized_fields[0],
                event_path=normalized_fields[1],
                asset_path=normalized_fields[2],
                bus_path=normalized_fields[3],
                bank_name=normalized_fields[4]
            )
            rows.append(row)
        
        return rows
    
    def read_file(self, filepath: str) -> List[CSVRow]:
        """
        Read and parse CSV from file path.
        
        Args:
            filepath: Path to CSV file.
            
        Returns:
            List of CSVRow namedtuples.
            
        Raises:
            CSVParseError: If CSV is invalid or malformed.
            FileNotFoundError: If file doesn't exist.
        """
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            return self.read(f)
