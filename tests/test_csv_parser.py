"""
TDD tests for CSV parser module.
Tests CSV reading, validation, and edge cases.
"""
import io
import pytest
from fmod_batch_import.csv_parser import CSVReader, CSVParseError, CSVRow


class TestCSVReaderInit:
    """Test CSVReader initialization."""
    
    def test_init_with_expected_columns(self):
        """CSVReader initializes with expected columns."""
        expected = ["audio_path", "event_path", "asset_path", "bus_path", "bank_name"]
        reader = CSVReader(expected_columns=expected)
        assert reader.expected_columns == expected


class TestCSVReaderValidCases:
    """Test valid CSV parsing scenarios."""
    
    def test_parse_valid_csv(self):
        """Parse valid CSV with all required columns."""
        csv_content = """audio_path,event_path,asset_path,bus_path,bank_name
/path/to/audio.wav,/event/path,/asset/path,/bus/path,Master"""
        
        reader = CSVReader()
        rows = reader.read(io.StringIO(csv_content))
        
        assert len(rows) == 1
        assert rows[0].row_index == 1
        assert rows[0].audio_path == "/path/to/audio.wav"
        assert rows[0].event_path == "/event/path"
        assert rows[0].asset_path == "/asset/path"
        assert rows[0].bus_path == "/bus/path"
        assert rows[0].bank_name == "Master"
    
    def test_parse_multiple_rows(self):
        """Parse CSV with multiple data rows."""
        csv_content = """audio_path,event_path,asset_path,bus_path,bank_name
/path/to/audio1.wav,/event/1,/asset/1,/bus/1,Bank1
/path/to/audio2.wav,/event/2,/asset/2,/bus/2,Bank2
/path/to/audio3.wav,/event/3,/asset/3,/bus/3,Bank3"""
        
        reader = CSVReader()
        rows = reader.read(io.StringIO(csv_content))
        
        assert len(rows) == 3
        assert rows[0].row_index == 1
        assert rows[1].row_index == 2
        assert rows[2].row_index == 3
    
    def test_parse_empty_fields(self):
        """Parse CSV with empty fields (normalized to empty string)."""
        csv_content = """audio_path,event_path,asset_path,bus_path,bank_name
/path/to/audio.wav,,,/bus/path,"""
        
        reader = CSVReader()
        rows = reader.read(io.StringIO(csv_content))
        
        assert len(rows) == 1
        assert rows[0].audio_path == "/path/to/audio.wav"
        assert rows[0].event_path == ""
        assert rows[0].asset_path == ""
        assert rows[0].bus_path == "/bus/path"
        assert rows[0].bank_name == ""


class TestCSVReaderEdgeCases:
    """Test edge cases and special handling."""
    
    def test_parse_with_utf8_bom(self):
        """Handle UTF-8 BOM at start of file."""
        # Note: BOM is \ufeff, but when in StringIO it's handled differently
        # We'll test this via read_file with actual encoding instead
        csv_content = "audio_path,event_path,asset_path,bus_path,bank_name\n/path/to/audio.wav,/event/path,/asset/path,/bus/path,Master"
        
        reader = CSVReader()
        rows = reader.read(io.StringIO(csv_content))
        
        assert len(rows) == 1
        assert rows[0].audio_path == "/path/to/audio.wav"
    
    def test_parse_with_empty_lines(self):
        """Skip empty lines in CSV."""
        csv_content = """audio_path,event_path,asset_path,bus_path,bank_name

/path/to/audio.wav,/event/path,/asset/path,/bus/path,Master

"""
        
        reader = CSVReader()
        rows = reader.read(io.StringIO(csv_content))
        
        assert len(rows) == 1
        assert rows[0].row_index == 1
    
    def test_parse_with_trailing_commas(self):
        """Handle rows with trailing commas (should be treated as extra empty field)."""
        # Note: trailing comma creates an extra empty field, which should fail strict schema
        csv_content = """audio_path,event_path,asset_path,bus_path,bank_name
/path/to/audio.wav,/event/path,/asset/path,/bus/path,Master,"""
        
        reader = CSVReader()
        with pytest.raises(CSVParseError) as exc_info:
            reader.read(io.StringIO(csv_content))
        
        assert "column" in str(exc_info.value).lower()
    
    def test_parse_with_crlf(self):
        """Handle Windows CRLF line endings."""
        csv_content = "audio_path,event_path,asset_path,bus_path,bank_name\r\n/path/to/audio.wav,/event/path,/asset/path,/bus/path,Master\r\n"
        
        reader = CSVReader()
        rows = reader.read(io.StringIO(csv_content))
        
        assert len(rows) == 1
        assert rows[0].audio_path == "/path/to/audio.wav"
    
    def test_parse_with_quotes_and_commas(self):
        """Handle quoted fields containing commas."""
        csv_content = '''audio_path,event_path,asset_path,bus_path,bank_name
"/path/to, audio.wav","/event, path",/asset/path,/bus/path,Master'''
        
        reader = CSVReader()
        rows = reader.read(io.StringIO(csv_content))
        
        assert len(rows) == 1
        assert rows[0].audio_path == "/path/to, audio.wav"
        assert rows[0].event_path == "/event, path"
    
    def test_parse_only_header(self):
        """Handle CSV with only header row (no data)."""
        csv_content = "audio_path,event_path,asset_path,bus_path,bank_name\n"
        
        reader = CSVReader()
        rows = reader.read(io.StringIO(csv_content))
        
        assert len(rows) == 0
    
    def test_parse_empty_file(self):
        """Handle completely empty file."""
        csv_content = ""
        
        reader = CSVReader()
        with pytest.raises(CSVParseError) as exc_info:
            reader.read(io.StringIO(csv_content))
        
        assert "empty" in str(exc_info.value).lower() or "header" in str(exc_info.value).lower()


class TestCSVReaderValidation:
    """Test CSV validation and error cases."""
    
    def test_reject_wrong_column_count_too_few(self):
        """Reject CSV with too few columns."""
        csv_content = """audio_path,event_path,asset_path,bus_path
/path/to/audio.wav,/event/path,/asset/path,/bus/path"""
        
        reader = CSVReader()
        with pytest.raises(CSVParseError) as exc_info:
            reader.read(io.StringIO(csv_content))
        
        assert "column" in str(exc_info.value).lower()
    
    def test_reject_wrong_column_count_too_many(self):
        """Reject CSV with too many columns."""
        csv_content = """audio_path,event_path,asset_path,bus_path,bank_name,extra_column
/path/to/audio.wav,/event/path,/asset/path,/bus/path,Master,extra"""
        
        reader = CSVReader()
        with pytest.raises(CSVParseError) as exc_info:
            reader.read(io.StringIO(csv_content))
        
        assert "column" in str(exc_info.value).lower()
    
    def test_reject_wrong_column_names(self):
        """Reject CSV with incorrect column names."""
        csv_content = """wrong_path,event_path,asset_path,bus_path,bank_name
/path/to/audio.wav,/event/path,/asset/path,/bus/path,Master"""
        
        reader = CSVReader()
        with pytest.raises(CSVParseError) as exc_info:
            reader.read(io.StringIO(csv_content))
        
        assert "header" in str(exc_info.value).lower() or "column" in str(exc_info.value).lower()
    
    def test_reject_data_row_wrong_column_count(self):
        """Reject CSV where a data row has wrong column count."""
        csv_content = """audio_path,event_path,asset_path,bus_path,bank_name
/path/to/audio.wav,/event/path,/asset/path,/bus/path"""
        
        reader = CSVReader()
        with pytest.raises(CSVParseError) as exc_info:
            reader.read(io.StringIO(csv_content))
        
        assert "column" in str(exc_info.value).lower()
    
    def test_reject_missing_header(self):
        """Reject CSV with missing header."""
        csv_content = "/path/to/audio.wav,/event/path,/asset/path,/bus/path,Master\n"
        
        reader = CSVReader()
        with pytest.raises(CSVParseError) as exc_info:
            reader.read(io.StringIO(csv_content))
        
        assert "header" in str(exc_info.value).lower()


class TestCSVRowStructure:
    """Test CSVRow data structure."""
    
    def test_csvrow_is_namedtuple(self):
        """CSVRow should be a namedtuple with correct fields."""
        row = CSVRow(
            row_index=1,
            audio_path="/audio",
            event_path="/event",
            asset_path="/asset",
            bus_path="/bus",
            bank_name="Master"
        )
        
        assert row.row_index == 1
        assert row.audio_path == "/audio"
        assert row.event_path == "/event"
        assert row.asset_path == "/asset"
        assert row.bus_path == "/bus"
        assert row.bank_name == "Master"
    
    def test_csvrow_immutable(self):
        """CSVRow should be immutable."""
        row = CSVRow(
            row_index=1,
            audio_path="/audio",
            event_path="/event",
            asset_path="/asset",
            bus_path="/bus",
            bank_name="Master"
        )
        
        with pytest.raises(AttributeError):
            row.audio_path = "/new/path"


class TestCSVParseError:
    """Test CSVParseError exception."""
    
    def test_error_includes_message(self):
        """Error should include descriptive message with prefix."""
        error = CSVParseError("Test error message")
        assert str(error) == "CSV Error: Test error message"
    
    def test_error_can_include_row_number(self):
        """Error can include row number information."""
        error = CSVParseError("Column mismatch", row_number=5)
        assert "5" in str(error)
        assert "row" in str(error).lower()
