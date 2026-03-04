"""
GUI dialog flow for FMOD Batch Import.

Provides tkinter file selection dialogs for:
- CSV file selection
- Audio directory selection

Supports test mode via FMOD_IMPORTER_TEST_MODE environment variable:
  FMOD_IMPORTER_TEST_MODE=1       → use fixture paths (auto-proceed)
  FMOD_IMPORTER_TEST_MODE=cancel  → simulate cancel (exit cleanly)
"""

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional, Tuple


TEST_MODE = os.environ.get("FMOD_IMPORTER_TEST_MODE", "")
FIXTURE_CSV = os.environ.get("FMOD_IMPORTER_FIXTURE_CSV", "")
FIXTURE_AUDIO_DIR = os.environ.get("FMOD_IMPORTER_FIXTURE_AUDIO_DIR", "")


def _root() -> tk.Tk:
    """Create and hide a root Tk window."""
    root = tk.Tk()
    root.withdraw()
    return root


def select_csv() -> Optional[str]:
    """
    Show a file dialog to select the CSV file.
    Returns the selected path, or None if cancelled.
    """
    if TEST_MODE == "cancel":
        return None
    if TEST_MODE and FIXTURE_CSV:
        return FIXTURE_CSV

    root = _root()
    path = filedialog.askopenfilename(
        title="Select Import CSV",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
    )
    root.destroy()
    return path or None


def select_audio_dir() -> Optional[str]:
    """
    Show a directory dialog to select the audio files directory.
    Returns the selected path, or None if cancelled.
    """
    if TEST_MODE == "cancel":
        return None
    if TEST_MODE and FIXTURE_AUDIO_DIR:
        return FIXTURE_AUDIO_DIR

    root = _root()
    path = filedialog.askdirectory(title="Select Audio Files Directory")
    root.destroy()
    return path or None


def show_error(title: str, message: str) -> None:
    """Show an error dialog."""
    if TEST_MODE:
        print(f"[ERROR] {title}: {message}", file=sys.stderr)
        return
    root = _root()
    messagebox.showerror(title, message)
    root.destroy()


def show_info(title: str, message: str) -> None:
    """Show an info dialog."""
    if TEST_MODE:
        print(f"[INFO] {title}: {message}")
        return
    root = _root()
    messagebox.showinfo(title, message)
    root.destroy()


def prompt_start_fmod() -> bool:
    """
    Ask user to start FMOD Studio and retry.
    Returns True if user wants to retry, False to cancel.
    """
    if TEST_MODE:
        return False
    root = _root()
    result = messagebox.askretrycancel(
        "FMOD Studio Not Running",
        "Could not connect to FMOD Studio.\n\n"
        "Please open FMOD Studio with your project and enable the scripting server,\n"
        "then click Retry.",
    )
    root.destroy()
    return result


def run_selection_flow() -> Tuple[Optional[str], Optional[str]]:
    """
    Run the full GUI selection flow.
    Returns (csv_path, audio_dir) or (None, None) if cancelled.
    """
    csv_path = select_csv()
    if not csv_path:
        return None, None

    audio_dir = select_audio_dir()
    if not audio_dir:
        return None, None

    return csv_path, audio_dir
