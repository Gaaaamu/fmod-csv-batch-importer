"""FMOD Studio audio import via JavaScript generation."""

import os


def import_audio_file(file_path: str, target_folder: str | None = None) -> str:
    """Generate JavaScript code to import an audio file into FMOD Studio.
    
    Args:
        file_path: Absolute path to the audio file (required by FMOD)
        target_folder: Optional target asset folder path in FMOD (e.g., "Audio/Weapons")
                      
    Returns:
        JavaScript code string that can be executed in FMOD Studio
        
    Raises:
        ValueError: If file_path is not an absolute path
    """
    if not os.path.isabs(file_path):
        raise ValueError(f"FMOD requires absolute file path, got: {file_path}")
    
    # Normalize path separators for JS string
    normalized_path = file_path.replace("\\", "/")
    
    js_lines = [
        "// Import audio file",
        f"var importedAsset = studio.project.importAudioFile('{normalized_path}');",
        "",
        "// Check if import succeeded",
        "if (importedAsset === null || importedAsset === undefined) {",
        f"    throw new Error('Failed to import audio file: {normalized_path}');",
        "}",
    ]
    
    if target_folder:
        # Normalize folder path and generate JS to move asset
        normalized_folder = target_folder.replace("\\", "/").strip("/")
        js_lines.extend([
            "",
            "// Move to target folder",
            f"var targetFolder = studio.project.workspace.getAssetFolder('{normalized_folder}');",
            "if (targetFolder !== null && targetFolder !== undefined) {",
            "    importedAsset.moveToFolder(targetFolder);",
            "} else {",
            "    // Create folder path if it doesn't exist",
            f"    targetFolder = studio.project.workspace.createAssetFolder('{normalized_folder}');",
            "    importedAsset.moveToFolder(targetFolder);",
            "}",
        ])
    
    js_lines.extend([
        "",
        "// Return the imported asset for verification",
        "importedAsset;",
    ])
    
    return "\n".join(js_lines)
