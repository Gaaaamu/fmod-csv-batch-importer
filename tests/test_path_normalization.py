"""Tests for path normalization module.

Covers:
- Event path normalization (with and without prefix)
- Bus path normalization
- Bank path normalization
- Invalid prefix rejection
- Empty field validation
- Disallowed character detection
"""

import pytest
from fmod_batch_import.path_normalizer import (
    PathNormalizer,
    ImportRow,
    PathValidationError
)


class TestEventPathNormalization:
    """Test event path normalization scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.normalizer = PathNormalizer()
    
    def test_event_path_with_prefix(self):
        """Event path with event:/ prefix should remain normalized."""
        result = self.normalizer.normalize_event_path("event:/sfx/gunshot")
        assert result == "event:/sfx/gunshot"
    
    def test_event_path_without_prefix(self):
        """Event path without prefix should auto-add event:/."""
        result = self.normalizer.normalize_event_path("sfx/gunshot")
        assert result == "event:/sfx/gunshot"
    
    def test_event_path_with_leading_slash(self):
        """Event path with leading slash should be handled correctly."""
        result = self.normalizer.normalize_event_path("/sfx/gunshot")
        assert result == "event:/sfx/gunshot"
    
    def test_event_path_nested(self):
        """Nested event paths should be normalized correctly."""
        result = self.normalizer.normalize_event_path("sfx/weapons/guns/pistol/fire")
        assert result == "event:/sfx/weapons/guns/pistol/fire"
    
    def test_event_path_with_prefix_and_root(self):
        """Event path with event:/ prefix and root path."""
        result = self.normalizer.normalize_event_path("event:/")
        assert result == "event:/"
    
    def test_event_path_whitespace_stripped(self):
        """Event path should have whitespace stripped."""
        result = self.normalizer.normalize_event_path("  sfx/gunshot  ")
        assert result == "event:/sfx/gunshot"


class TestBusPathNormalization:
    """Test bus path normalization scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.normalizer = PathNormalizer()
    
    def test_bus_path_with_prefix(self):
        """Bus path with bus:/ prefix should remain normalized."""
        result = self.normalizer.normalize_bus_path("bus:/sfx")
        assert result == "bus:/sfx"
    
    def test_bus_path_without_prefix(self):
        """Bus path without prefix should auto-add bus:/."""
        result = self.normalizer.normalize_bus_path("sfx")
        assert result == "bus:/sfx"
    
    def test_bus_path_empty(self):
        """Empty bus path should return empty string."""
        result = self.normalizer.normalize_bus_path("")
        assert result == ""
    
    def test_bus_path_whitespace_only(self):
        """Whitespace-only bus path should return empty string."""
        result = self.normalizer.normalize_bus_path("   ")
        assert result == ""


class TestBankPathNormalization:
    """Test bank path normalization scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.normalizer = PathNormalizer()
    
    def test_bank_path_with_prefix(self):
        """Bank path with bank:/ prefix should remain normalized."""
        result = self.normalizer.normalize_bank_path("bank:/SFX")
        assert result == "bank:/SFX"
    
    def test_bank_path_without_prefix(self):
        """Bank path without prefix should auto-add bank:/."""
        result = self.normalizer.normalize_bank_path("SFX")
        assert result == "bank:/SFX"
    
    def test_bank_path_empty(self):
        """Empty bank path should return empty string."""
        result = self.normalizer.normalize_bank_path("")
        assert result == ""
    
    def test_bank_path_whitespace_only(self):
        """Whitespace-only bank path should return empty string."""
        result = self.normalizer.normalize_bank_path("   ")
        assert result == ""


class TestInvalidPrefixRejection:
    """Test that invalid path prefixes are rejected."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.normalizer = PathNormalizer()
    
    def test_event_path_with_bus_prefix(self):
        """Event path with bus: prefix should raise validation error."""
        with pytest.raises(PathValidationError) as exc_info:
            self.normalizer.normalize_event_path("bus:/sfx/gunshot")
        
        assert "Invalid event path prefix" in str(exc_info.value)
        assert "bus" in str(exc_info.value)
    
    def test_event_path_with_bank_prefix(self):
        """Event path with bank: prefix should raise validation error."""
        with pytest.raises(PathValidationError) as exc_info:
            self.normalizer.normalize_event_path("bank:/SFX")
        
        assert "Invalid event path prefix" in str(exc_info.value)
    
    def test_event_path_with_vca_prefix(self):
        """Event path with vca: prefix should raise validation error."""
        with pytest.raises(PathValidationError) as exc_info:
            self.normalizer.normalize_event_path("vca:/master")
        
        assert "Invalid event path prefix" in str(exc_info.value)
    
    def test_bus_path_with_event_prefix(self):
        """Bus path with event: prefix should raise validation error."""
        with pytest.raises(PathValidationError) as exc_info:
            self.normalizer.normalize_bus_path("event:/sfx")
        
        assert "Invalid bus path prefix" in str(exc_info.value)
    
    def test_bus_path_with_bank_prefix(self):
        """Bus path with bank: prefix should raise validation error."""
        with pytest.raises(PathValidationError) as exc_info:
            self.normalizer.normalize_bus_path("bank:/SFX")
        
        assert "Invalid bus path prefix" in str(exc_info.value)
    
    def test_bank_path_with_event_prefix(self):
        """Bank path with event: prefix should raise validation error."""
        with pytest.raises(PathValidationError) as exc_info:
            self.normalizer.normalize_bank_path("event:/sfx")
        
        assert "Invalid bank path prefix" in str(exc_info.value)
    
    def test_bank_path_with_bus_prefix(self):
        """Bank path with bus: prefix should raise validation error."""
        with pytest.raises(PathValidationError) as exc_info:
            self.normalizer.normalize_bank_path("bus:/sfx")
        
        assert "Invalid bank path prefix" in str(exc_info.value)


class TestEmptyFieldValidation:
    """Test that empty required fields are detected."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.normalizer = PathNormalizer()
    
    def test_empty_event_path_raises_error(self):
        """Empty event_path should raise validation error."""
        with pytest.raises(PathValidationError) as exc_info:
            self.normalizer.normalize_event_path("")
        
        assert "cannot be empty" in str(exc_info.value)
        assert "event_path" in str(exc_info.value)
    
    def test_whitespace_only_event_path_raises_error(self):
        """Whitespace-only event_path should raise validation error."""
        with pytest.raises(PathValidationError) as exc_info:
            self.normalizer.normalize_event_path("   ")
        
        assert "cannot be empty" in str(exc_info.value)
    
    def test_empty_audio_path_in_row_raises_error(self):
        """Empty audio_path in row should raise validation error."""
        with pytest.raises(PathValidationError) as exc_info:
            self.normalizer.normalize_row(
                audio_path="",
                event_path="event:/sfx/gunshot",
                row_index=5
            )
        
        assert "cannot be empty" in str(exc_info.value)
        assert "audio_path" in str(exc_info.value)
        assert "Row 5" in str(exc_info.value)
    
    def test_empty_event_path_in_row_raises_error(self):
        """Empty event_path in row should raise validation error."""
        with pytest.raises(PathValidationError) as exc_info:
            self.normalizer.normalize_row(
                audio_path="sounds/gunshot.wav",
                event_path="",
                row_index=10
            )
        
        assert "cannot be empty" in str(exc_info.value)
        assert "event_path" in str(exc_info.value)
        assert "Row 10" in str(exc_info.value)
    
    def test_empty_optional_fields_allowed(self):
        """Empty optional fields (bus, bank) should be allowed."""
        result = self.normalizer.normalize_row(
            audio_path="sounds/gunshot.wav",
            event_path="event:/sfx/gunshot",
            bus_path="",
            bank_name="",
            row_index=1
        )
        
        assert result.bus_path == ""
        assert result.bank_name == ""


class TestDisallowedCharacterDetection:
    """Test that disallowed characters are detected in paths."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.normalizer = PathNormalizer()
    
    def test_event_path_with_less_than(self):
        """Event path with < should raise validation error."""
        with pytest.raises(PathValidationError) as exc_info:
            self.normalizer.normalize_event_path("event:/sfx/<gunshot")
        
        assert "disallowed characters" in str(exc_info.value)
        assert "'<'" in str(exc_info.value)
    
    def test_event_path_with_greater_than(self):
        """Event path with > should raise validation error."""
        with pytest.raises(PathValidationError) as exc_info:
            self.normalizer.normalize_event_path("event:/sfx/gunshot>")
        
        assert "disallowed characters" in str(exc_info.value)
        assert "'>'" in str(exc_info.value)
    
    def test_event_path_with_pipe(self):
        """Event path with | should raise validation error."""
        with pytest.raises(PathValidationError) as exc_info:
            self.normalizer.normalize_event_path("event:/sfx/gun|shot")
        
        assert "disallowed characters" in str(exc_info.value)
        assert "'|'" in str(exc_info.value)
    
    def test_event_path_with_question_mark(self):
        """Event path with ? should raise validation error."""
        with pytest.raises(PathValidationError) as exc_info:
            self.normalizer.normalize_event_path("event:/sfx/gun?shot")
        
        assert "disallowed characters" in str(exc_info.value)
        assert "'?'" in str(exc_info.value)
    
    def test_event_path_with_asterisk(self):
        """Event path with * should raise validation error."""
        with pytest.raises(PathValidationError) as exc_info:
            self.normalizer.normalize_event_path("event:/sfx/gun*shot")
        
        assert "disallowed characters" in str(exc_info.value)
        assert "'*'" in str(exc_info.value)
    
    def test_event_path_with_backslash(self):
        """Event path with \\ should raise validation error."""
        with pytest.raises(PathValidationError) as exc_info:
            self.normalizer.normalize_event_path("event:/sfx/gun\\shot")
        
        assert "disallowed characters" in str(exc_info.value)
        assert "'\\'" in str(exc_info.value)
    
    def test_event_path_with_quote(self):
        """Event path with \" should raise validation error."""
        with pytest.raises(PathValidationError) as exc_info:
            self.normalizer.normalize_event_path('event:/sfx/gun"shot')
        
        assert "disallowed characters" in str(exc_info.value)
        assert '"' in str(exc_info.value)
    
    def test_bus_path_with_disallowed_chars(self):
        """Bus path with disallowed characters should raise validation error."""
        with pytest.raises(PathValidationError) as exc_info:
            self.normalizer.normalize_bus_path("bus:/sfx>weapons")
        
        assert "disallowed characters" in str(exc_info.value)
    
    def test_bank_path_with_disallowed_chars(self):
        """Bank path with disallowed characters should raise validation error."""
        with pytest.raises(PathValidationError) as exc_info:
            self.normalizer.normalize_bank_path("bank:/SFX|Master")
        
        assert "disallowed characters" in str(exc_info.value)
    
    def test_multiple_disallowed_chars_reported(self):
        """Multiple disallowed characters should all be reported."""
        with pytest.raises(PathValidationError) as exc_info:
            self.normalizer.normalize_event_path("event:/sfx/<gun*|shot>")
        
        error_msg = str(exc_info.value)
        assert "disallowed characters" in error_msg
        assert "'<'" in error_msg
        assert "'>'" in error_msg
        assert "'*'" in error_msg
        assert "'|'" in error_msg


class TestRowMapping:
    """Test complete row mapping to ImportRow structure."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.normalizer = PathNormalizer()
    
    def test_full_row_normalization(self):
        """Complete row should normalize all fields correctly."""
        result = self.normalizer.normalize_row(
            audio_path="/audio/gunshot.wav",
            event_path="sfx/weapons/gunshot",
            asset_path="assets/weapons",
            bus_path="sfx",
            bank_name="SFX",
            row_index=3
        )
        
        assert isinstance(result, ImportRow)
        assert result.audio_path == "/audio/gunshot.wav"
        assert result.event_path == "event:/sfx/weapons/gunshot"
        assert result.asset_path == "assets/weapons"
        assert result.bus_path == "bus:/sfx"
        assert result.bank_name == "bank:/SFX"
        assert result.row_index == 3
    
    def test_row_with_prefixed_paths(self):
        """Row with already-prefixed paths should remain correct."""
        result = self.normalizer.normalize_row(
            audio_path="/audio/explosion.wav",
            event_path="event:/sfx/explosion",
            bus_path="bus:/sfx",
            bank_name="bank:/Master",
            row_index=1
        )
        
        assert result.event_path == "event:/sfx/explosion"
        assert result.bus_path == "bus:/sfx"
        assert result.bank_name == "bank:/Master"
    
    def test_row_preserves_warnings(self):
        """Row should preserve warnings list."""
        result = self.normalizer.normalize_row(
            audio_path="/audio/test.wav",
            event_path="event:/test",
            row_index=0
        )
        
        assert isinstance(result.warnings, list)
        assert len(result.warnings) == 0


class TestValidatePrefix:
    """Test the validate_prefix helper method."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.normalizer = PathNormalizer()
    
    def test_validate_prefix_matching(self):
        """Valid matching prefix should return True."""
        result = self.normalizer.validate_prefix("event:/sfx", "event")
        assert result is True
    
    def test_validate_prefix_no_prefix(self):
        """Path with no prefix should return True (auto-prefix allowed)."""
        result = self.normalizer.validate_prefix("sfx/gunshot", "event")
        assert result is True
    
    def test_validate_prefix_mismatch(self):
        """Mismatched prefix should raise validation error."""
        with pytest.raises(PathValidationError) as exc_info:
            self.normalizer.validate_prefix("bus:/sfx", "event")
        
        assert "Invalid prefix" in str(exc_info.value)
    
    def test_validate_prefix_empty_path(self):
        """Empty path should return True."""
        result = self.normalizer.validate_prefix("", "event")
        assert result is True
