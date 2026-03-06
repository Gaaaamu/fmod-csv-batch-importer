"""Path normalization module for FMOD batch import.

Normalizes FMOD paths according to FMOD Studio scripting conventions:
- event paths: event:/path/to/event or path/to/event (auto-prefix)
- bus paths: bus:/path/to/bus
- bank paths: bank:/path/to/bank
"""

from dataclasses import dataclass, field
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
    warnings: list[str] = field(default_factory=list)


class PathValidationError(Exception):
    """Raised when path validation fails."""
    pass


class PathNormalizer:
    """Normalizes and validates FMOD paths according to FMOD conventions.
    
    FMOD path format: type:/path/to/item
    Valid types: event, bus, bank, vca, asset, etc.
    """
    
    # Valid FMOD path types
    VALID_TYPES: set[str] = {"event", "bus", "bank", "vca", "asset"}
    
    # Required types that cannot be empty when specified
    REQUIRED_EVENT_FIELDS: set[str] = {"audio_path", "event_path"}
    
    # Disallowed characters in FMOD path parts (based on FMOD Studio conventions)
    # Note: ':' is allowed in the prefix but not in the path portion
    DISALLOWED_IN_PATH_PART: set[str] = {'<', '>', ':', '"', '|', '?', '*', '\\'}
    
    # Pattern for valid FMOD path: type:/path/to/item
    # Pattern for valid FMOD path: type:/path/to/item
    FMOD_PATH_PATTERN: re.Pattern[str] = re.compile(r'^(\w+):(/.*)?$')
    
    audio_dir: str | None
    event_folder_supported: bool
    template_event_path: str | None
    template_bus_path: str | None
    template_bank_name: str | None
    
    def __init__(
        self,
        audio_dir: str | None = None,
        template_event_path: str | None = None,
        template_bus_path: str | None = None,
        template_bank_name: str | None = None,
        event_folder_supported: bool = False
    ):
        """Initialize the path normalizer.
        
        Args:
            audio_dir: Base directory for audio files (for computing asset_path defaults)
            template_event_path: Template event path for event_path default generation
            template_bus_path: Template bus path for bus_path inheritance
            template_bank_name: Template bank name for bank_name inheritance
            event_folder_supported: Whether nested event folders can be created
        """
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.audio_dir = audio_dir
        self.event_folder_supported = event_folder_supported
        self.template_event_path = template_event_path if template_event_path else None
        self.template_bus_path = template_bus_path
        self.template_bank_name = template_bank_name
    
    def _get_template_folder(self) -> str:
        """Extract folder path from template event path.
        
        Returns:
            Folder path (e.g., 'VO/Narration/Battle' from 'event:/VO/Narration/Battle/TemplateEvent'),
            or empty string if no template is configured.
        """
        if not self.template_event_path:
            return ""
        path_type, remaining = self._extract_path_type(self.template_event_path)
        if path_type == "event" and remaining:
            # Remove leading slash and get folder path (everything except last component)
            path = remaining.lstrip('/')
            if '/' in path:
                return path.rsplit('/', 1)[0]
        return ""
    
    def _get_audio_name(self, audio_path: str) -> str:
        """Extract audio filename without extension.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Audio name without extension
        """
        from pathlib import Path
        return Path(audio_path).stem
    
    def _compute_asset_path_default(self, audio_path: str) -> str:
        """Compute default asset_path from audio_path relative to base directory.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Relative path under audio directory (without filename)
        """
        if not self.audio_dir:
            return ""
        
        from pathlib import Path
        try:
            audio_file = Path(audio_path)
            base = Path(self.audio_dir)
            
            # If audio_path is absolute and under base, compute relative path
            if audio_file.is_absolute():
                try:
                    rel_path = audio_file.relative_to(base)
                    # Return parent directory of the file
                    return str(rel_path.parent) if rel_path.parent != Path('.') else ""
                except ValueError:
                    # Not under base directory
                    return ""
            else:
                # Relative path - return parent directory
                return str(audio_file.parent) if audio_file.parent != Path('.') else ""
        except Exception:
            return ""
    
    def _apply_defaults(
        self,
        audio_path: str,
        event_path: str,
        asset_path: str,
        bus_path: str,
        bank_name: str
    ) -> tuple[str, str, str, str, str]:
        """Apply default rules for empty fields.
        
        Default rules (per confirmed spec):
        - asset_path: if empty, use audio file's relative path under audio directory
        - event_path: if empty, generate event:/<template folder>/<audio_name>
        - bus_path: if empty, inherit from template or fallback to default bus
        - bank_name: if empty, inherit from template or fallback to default bank
        
        Args:
            audio_path: Path to audio file (required)
            event_path: FMOD event path (may be empty)
            asset_path: Target asset folder path (may be empty)
            bus_path: FMOD bus path (may be empty)
            bank_name: FMOD bank name (may be empty)
            
        Returns:
            Tuple of (audio_path, event_path, asset_path, bus_path, bank_name) with defaults applied
        """
        audio_path = audio_path.strip() if audio_path else ""
        event_path = event_path.strip() if event_path else ""
        asset_path = asset_path.strip() if asset_path else ""
        bus_path = bus_path.strip() if bus_path else ""
        bank_name = bank_name.strip() if bank_name else ""
        
        # Get audio name for event_path generation
        audio_name = self._get_audio_name(audio_path) if audio_path else ""
        
        # Rule 1: asset_path default
        if not asset_path and audio_path:
            asset_path = self._compute_asset_path_default(audio_path)
            if asset_path:
                self.warnings.append(f"asset_path default applied: {asset_path}")
        
        # Rule 2: event_path default
        if not event_path and audio_name:
            template_folder = self._get_template_folder()
            if template_folder:
                default_event_path = f"event:/{template_folder}/{audio_name}"
            else:
                default_event_path = f"event:/{audio_name}"

            event_path = default_event_path
            self.warnings.append(f"event_path default applied: {default_event_path}")

            if template_folder and not self.event_folder_supported:
                fallback_path = f"event:/{audio_name}"
                event_path = fallback_path
                self.warnings.append(
                    f"event_path folder unsupported; using root-level event: {fallback_path}"
                )
        
        # Rule 3: bus_path — inherit from template if provided, otherwise leave empty
        if not bus_path and self.template_bus_path:
            bus_path = self.template_bus_path
            self.warnings.append(f"bus_path inherited from template: {bus_path}")

        # Rule 4: bank_name — inherit from template if provided, otherwise leave empty
        if not bank_name and self.template_bank_name:
            bank_name = self.template_bank_name
            self.warnings.append(f"bank_name inherited from template: {bank_name}")
        
        return audio_path, event_path, asset_path, bus_path, bank_name
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
        found_chars: list[str] = []
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
    
    def _extract_path_type(self, path: str) -> tuple[str | None, str]:
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
            event_path: FMOD event path (optional, auto-generated from audio_path if empty)
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
        
        # Apply confirmed default rules for empty fields
        # Rules:
        # - asset_path: if empty, use audio file's relative path under audio directory
        # - event_path: if empty, generate event:/<template folder>/<audio_name>
        # - bus_path: if empty, inherit from template or fallback to default bus
        # - bank_name: if empty, inherit from template or fallback to default bank
        audio_path, event_path, asset_path, bus_path, bank_name = self._apply_defaults(
            audio_path, event_path, asset_path, bus_path, bank_name
        )
        
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
            audio_path=audio_path,
            event_path=normalized_event,
            asset_path=asset_path,
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
