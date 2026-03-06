"""
DEPRECATED — Metadata verification utility for FMOD batch import.

This module was an experimental debugging utility to inspect FMOD event XML
files for SingleSound/audioFile relationships. It is not integrated into the
main import pipeline and is not called from anywhere in the codebase.

Do not use or extend this module.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional


class VerificationStatus(Enum):
    """Verification result status."""
    OK = "ok"
    MISSING_SOUND = "missing_sound"
    MISSING_AUDIOFILE = "missing_audiofile"


@dataclass
class SingleSoundInfo:
    """Information about a SingleSound object."""
    id: str
    has_audio_file: bool
    audio_file_id: Optional[str]


@dataclass
class VerificationResult:
    """Result of metadata verification."""
    status: VerificationStatus
    event_name: Optional[str]
    single_sounds: List[SingleSoundInfo]
    errors: List[str]


def parse_event_metadata(xml_path: Path) -> Optional[ET.Element]:
    """Parse FMOD event metadata XML file.
    
    Args:
        xml_path: Path to the XML metadata file
        
    Returns:
        Root element of the parsed XML, or None if parsing fails
    """
    try:
        tree = ET.parse(xml_path)
        return tree.getroot()
    except ET.ParseError as e:
        return None
    except FileNotFoundError:
        return None


def extract_event_name(root: ET.Element) -> Optional[str]:
    """Extract event name from metadata.
    
    Args:
        root: Root element of the parsed XML
        
    Returns:
        Event name if found, None otherwise
    """
    # Find Event object
    for obj in root.findall(".//object[@class='Event']"):
        name_elem = obj.find(".//property[@name='name']/value")
        if name_elem is not None:
            return name_elem.text
    return None


def find_single_sounds(root: ET.Element) -> List[SingleSoundInfo]:
    """Find all SingleSound objects and their audioFile relationships.
    
    Args:
        root: Root element of the parsed XML
        
    Returns:
        List of SingleSoundInfo objects
    """
    single_sounds = []
    
    for obj in root.findall(".//object[@class='SingleSound']"):
        sound_id = obj.get("id", "")
        
        # Check for audioFile relationship
        audio_file_rel = obj.find(".//relationship[@name='audioFile']")
        has_audio_file = audio_file_rel is not None
        audio_file_id = None
        
        if has_audio_file:
            dest = audio_file_rel.find("destination")
            if dest is not None:
                audio_file_id = dest.text
        
        single_sounds.append(SingleSoundInfo(
            id=sound_id,
            has_audio_file=has_audio_file,
            audio_file_id=audio_file_id
        ))
    
    return single_sounds


def verify_event_metadata(xml_path: Path) -> VerificationResult:
    """Verify FMOD event metadata for SingleSound + audioFile relationships.
    
    This is a READ-ONLY verification function. It does not modify any files.
    
    Args:
        xml_path: Path to the event metadata XML file
        
    Returns:
        VerificationResult containing status and details
        
    Example:
        >>> result = verify_event_metadata(Path("event.xml"))
        >>> print(result.status)  # VerificationStatus.OK
    """
    errors = []
    
    # Parse XML
    root = parse_event_metadata(xml_path)
    if root is None:
        return VerificationResult(
            status=VerificationStatus.MISSING_SOUND,
            event_name=None,
            single_sounds=[],
            errors=["Failed to parse XML file"]
        )
    
    # Extract event name
    event_name = extract_event_name(root)
    
    # Find SingleSound objects
    single_sounds = find_single_sounds(root)
    
    # Determine status
    if not single_sounds:
        status = VerificationStatus.MISSING_SOUND
        errors.append("No SingleSound objects found in event")
    else:
        missing_audio_files = [s for s in single_sounds if not s.has_audio_file]
        if missing_audio_files:
            status = VerificationStatus.MISSING_AUDIOFILE
            errors.append(f"{len(missing_audio_files)} SingleSound(s) missing audioFile relationship")
        else:
            status = VerificationStatus.OK
    
    return VerificationResult(
        status=status,
        event_name=event_name,
        single_sounds=single_sounds,
        errors=errors
    )


def format_verification_report(result: VerificationResult) -> str:
    """Format verification result as a human-readable report.
    
    Args:
        result: VerificationResult to format
        
    Returns:
        Formatted report string
    """
    lines = [
        "=" * 50,
        "FMOD Event Metadata Verification Report",
        "=" * 50,
        f"Event Name: {result.event_name or 'Unknown'}",
        f"Status: {result.status.value}",
        f"SingleSound Objects: {len(result.single_sounds)}",
        "-" * 50,
    ]
    
    if result.single_sounds:
        lines.append("SingleSound Details:")
        for sound in result.single_sounds:
            audio_status = f"OK ({sound.audio_file_id})" if sound.has_audio_file else "MISSING"
            lines.append(f"  - ID: {sound.id}")
            lines.append(f"    audioFile: {audio_status}")
    
    if result.errors:
        lines.append("-" * 50)
        lines.append("Errors:")
        for error in result.errors:
            lines.append(f"  - {error}")
    
    lines.append("=" * 50)
    return "\n".join(lines)


if __name__ == "__main__":
    # Test with template event
    test_path = Path("Fmod Test/batch test/Metadata/Event/{3e7baf7c-881f-412d-8733-2117d10e4dcb}.xml")
    if test_path.exists():
        result = verify_event_metadata(test_path)
        print(format_verification_report(result))
    else:
        print(f"Test file not found: {test_path}")
