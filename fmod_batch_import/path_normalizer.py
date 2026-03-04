"""Path normalization module for FMOD batch import.

Normalizes FMOD paths according to FMOD Studio scripting conventions:
- event paths: event:/path/to/event or path/to/event (auto-prefix)
- bus paths: bus:/path/to/bus
- bank paths: bank:/path/to/bank
"""

from dataclasses import dataclass, field
from typing import List, Optional, Set
import re


@dataclass
class ImportRow:
    """Normalized import row structure.
    
    Fields:
        audio_path: Path to audio file (required)
        event_path: Normalized FMOD event path with event:/ prefix (required)
        asset_path: Target asset folder path (optional)
        bus_path: Normalized FMOD bus path with bus:/ prefix (optional)
        bank_name: Normalized FMOD bank path with bank:/ prefix (optional)
        row_index: Original CSV row index for error reporting
        warnings: List of non-fatal warnings
    """
    audio_path: str
    event_path: str
    asset_path: str = ""
    bus_path: str = ""
    bank_name: str = ""
    row_index: int = 0
    warnings: List[str] = field(default_factory=list)


class PathValidationError(Exception):
    """Raised when path validation fails."""
    pass


class PathNormalizer:
    """Normalizes and validates FMOD paths according to FMOD conventions.
    
    FMOD path format: type:/path/to/item
    Valid types: event, bus, bank, vca, asset, etc.
    """
    
    # Valid FMOD path types
    VALID_TYPES: Set[str] = {"event", "bus", "bank", "vca", "asset"}
    
    # Required types that cannot be empty when specified
    REQUIRED_EVENT_FIELDS: Set[str] = {"audio_path", "event_path"}
    
    # Disallowed characters in FMOD path parts (based on FMOD Studio conventions)
    # Note: ':' is allowed in the prefix but not in the path portion
    DISALLOWED_IN_PATH_PART: Set[str] = {'<', '>', ':', '"', '|', '?', '*', '\\'}
    
    # Pattern for valid FMOD path: type:/path/to/item
    FMOD_PATH_PATTERN = re.compile(r'^(\w+):(/.*)?$')
    
    def __init__(self):
        """Initialize the path normalizer."""
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def _validate_not_empty(self, value: str, field_name: str) -> None:
        """Validate that a required field is not empty.
        
        Args:
            value: The field value to check
            field_name: Name of the field for error messages
            
        Raises:
            PathValidationError: If the field is empty or whitespace-only
        """
        if not value or not value.strip():
            raise PathValidationError(f"Required field '{field_name}' cannot be empty")
    
    def _validate_disallowed_chars(self, path_part: str, field_name: str) -> None:
        """Validate that path part does not contain disallowed characters.
        
        Args:
            path_part: The path segment to validate (without type prefix)
            field_name: Name of the field for error messages
            
        Raises:
            PathValidationError: If disallowed characters are found
        """
        found_chars = []
        for char in self.DISALLOWED_IN_PATH_PART:
            if char in path_part:
                found_chars.append(char)
        
        if found_chars:
            chars_str = ', '.join(f"'{c}'" for c in found_chars)
            raise PathValidationError(
                f"Field '{field_name}' contains disallowed characters: {chars_str}"
            )
    
    def _validate_path_chars(self, path: str, field_name: str) -> None:
        """Validate that FMOD path (with prefix) doesn't have disallowed chars in path portion.
        
        The type prefix (e.g., 'event:') is allowed to contain ':', but the path
        portion after the prefix is checked for all disallowed characters.
        
        Args:
            path: The full FMOD path to validate
            field_name: Name of the field for error messages
            
        Raises:
            PathValidationError: If disallowed characters are found in path portion
        """
        # Extract just the path part (after type:/)
        path_type, remaining = self._extract_path_type(path)
        
        if path_type is not None:
            # Has a prefix - validate only the remaining path part
            if remaining and remaining != "/":
                self._validate_disallowed_chars(remaining, field_name)
        else:
            # No prefix - validate the whole path
            self._validate_disallowed_chars(path, field_name)
    
    def _extract_path_type(self, path: str) -> tuple[Optional[str], str]:
        """Extract the type prefix from a FMOD path.
        
        Args:
            path: The path to parse
            
        Returns:
            Tuple of (type_prefix, remaining_path) or (None, original_path) if no prefix
        """
        match = self.FMOD_PATH_PATTERN.match(path)
        if match:
            return match.group(1), match.group(2) or "/"
        return None, path
    
    def normalize_event_path(self, path: str) -> str:
        """Normalize an event path to FMOD format (event:/path).
        
        Handles paths with or without 'event:/' prefix.
        
        Args:
            path: The event path to normalize
            
        Returns:
            Normalized path with event:/ prefix
            
        Raises:
            PathValidationError: If path has invalid format or disallowed characters
        """
        self._validate_not_empty(path, "event_path")
        path = path.strip()
        self._validate_path_chars(path, "event_path")
        self._validate_path_chars(path, "event_path")
        
        path_type, remaining = self._extract_path_type(path)
        
        if path_type is None:
            # No prefix - auto-add event:/
            normalized = f"event:/{path.lstrip('/')}"
        elif path_type == "event":
            # Already has event: prefix, ensure proper format
            normalized = f"event:{remaining}"
        else:
            # Wrong prefix type
            raise PathValidationError(
                f"Invalid event path prefix '{path_type}:' - expected 'event:' or no prefix"
            )
        
        return normalized
    
    def normalize_bus_path(self, path: str) -> str:
        """Normalize a bus path to FMOD format (bus:/path).
        
        Args:
            path: The bus path to normalize
            
        Returns:
            Normalized path with bus:/ prefix
            
        Raises:
            PathValidationError: If path has invalid format or disallowed characters
        """
        if not path or not path.strip():
            return ""  # Bus path is optional
        
        self._validate_path_chars(path, "bus_path")
        
        path_type, remaining = self._extract_path_type(path)
        
        if path_type is None:
            # No prefix - auto-add bus:/
            normalized = f"bus:/{path.lstrip('/')}"
        elif path_type == "bus":
            # Already has bus: prefix
            normalized = f"bus:{remaining}"
        else:
            # Wrong prefix type
            raise PathValidationError(
                f"Invalid bus path prefix '{path_type}:' - expected 'bus:' or no prefix"
            )
        
        return normalized
    
    def normalize_bank_path(self, path: str) -> str:
        """Normalize a bank path to FMOD format (bank:/path).
        
        Args:
            path: The bank path to normalize
            
        Returns:
            Normalized path with bank:/ prefix
            
        Raises:
            PathValidationError: If path has invalid format or disallowed characters
        """
        if not path or not path.strip():
            return ""  # Bank path is optional
        
        self._validate_path_chars(path, "bank_name")
        
        path_type, remaining = self._extract_path_type(path)
        
        if path_type is None:
            # No prefix - auto-add bank:/
            normalized = f"bank:/{path.lstrip('/')}"
        elif path_type == "bank":
            # Already has bank: prefix
            normalized = f"bank:{remaining}"
        else:
            # Wrong prefix type
            raise PathValidationError(
                f"Invalid bank path prefix '{path_type}:' - expected 'bank:' or no prefix"
            )
        
        return normalized
    
    def normalize_row(
        self,
        audio_path: str,
        event_path: str,
        asset_path: str = "",
        bus_path: str = "",
        bank_name: str = "",
        row_index: int = 0
    ) -> ImportRow:
        """Normalize a complete CSV row to ImportRow structure.
        
        Args:
            audio_path: Path to audio file (required)
            event_path: FMOD event path (required)
            asset_path: Target asset folder path (optional)
            bus_path: FMOD bus path (optional)
            bank_name: FMOD bank path (optional)
            row_index: Original CSV row index for error reporting
            
        Returns:
            ImportRow with all paths normalized
            
        Raises:
            PathValidationError: If required fields are missing or invalid
        """
        self.errors = []
        self.warnings = []
        
        # Validate required fields
        try:
            self._validate_not_empty(audio_path, "audio_path")
        except PathValidationError as e:
            self.errors.append(str(e))
        
        try:
            self._validate_not_empty(event_path, "event_path")
        except PathValidationError as e:
            self.errors.append(str(e))
        
        # Normalize paths
        normalized_event = ""
        normalized_bus = ""
        normalized_bank = ""
        
        try:
            normalized_event = self.normalize_event_path(event_path)
        except PathValidationError as e:
            self.errors.append(str(e))
        
        try:
            normalized_bus = self.normalize_bus_path(bus_path)
        except PathValidationError as e:
            self.errors.append(str(e))
        
        try:
            normalized_bank = self.normalize_bank_path(bank_name)
        except PathValidationError as e:
            self.errors.append(str(e))
        
        # Check if there were any errors
        if self.errors:
            raise PathValidationError(
                f"Row {row_index}: " + "; ".join(self.errors)
            )
        
        return ImportRow(
            audio_path=audio_path.strip(),
            event_path=normalized_event,
            asset_path=asset_path.strip() if asset_path else "",
            bus_path=normalized_bus,
            bank_name=normalized_bank,
            row_index=row_index,
            warnings=self.warnings.copy()
        )
    
    def validate_prefix(self, path: str, expected_type: str) -> bool:
        """Validate that a path has the expected prefix type.
        
        Args:
            path: The path to validate
            expected_type: Expected prefix type (event, bus, bank, etc.)
            
        Returns:
            True if prefix matches or path has no prefix (auto-prefix allowed)
            
        Raises:
            PathValidationError: If prefix exists but doesn't match expected type
        """
        if not path:
            return True
        
        path_type, _ = self._extract_path_type(path)
        
        if path_type is None:
            return True  # No prefix, will auto-add
        
        if path_type != expected_type:
            raise PathValidationError(
                f"Invalid prefix '{path_type}:' - expected '{expected_type}:'"
            )
        
        return True
