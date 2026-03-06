"""
GUI dialog flow for FMOD Batch Import.

Provides tkinter file selection dialogs for:
- CSV file selection
- Audio directory selection
- Template event path selection

Last-used paths are persisted in ~/.fmod_batch_import.json across sessions.

Supports test mode via FMOD_IMPORTER_TEST_MODE environment variable:
  FMOD_IMPORTER_TEST_MODE=1       → use fixture paths (auto-proceed)
  FMOD_IMPORTER_TEST_MODE=cancel  → simulate cancel (exit cleanly)
"""

import json
import os
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


TEST_MODE = os.environ.get("FMOD_IMPORTER_TEST_MODE", "")
FIXTURE_CSV = os.environ.get("FMOD_IMPORTER_FIXTURE_CSV", "")
FIXTURE_AUDIO_DIR = os.environ.get("FMOD_IMPORTER_FIXTURE_AUDIO_DIR", "")

_SETTINGS_FILE = Path.home() / ".fmod_batch_import.json"


def _load_settings() -> dict[str, str]:
    """Load persisted settings from disk. Returns empty dict on any error."""
    try:
        data = json.loads(_SETTINGS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def _save_settings(settings: dict[str, str]) -> None:
    """Persist settings to disk. Silently ignores write errors."""
    try:
        _SETTINGS_FILE.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    except OSError:
        pass


def _root() -> tk.Tk:
    """Create and hide a root Tk window."""
    root = tk.Tk()
    root.withdraw()
    return root


class BatchImportDialog:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("FMOD Batch Import")
        self.root.geometry("600x450")

        settings = _load_settings()

        self.csv_path = tk.StringVar(value=settings.get("csv_path", ""))
        self.audio_dir = tk.StringVar(value=settings.get("audio_dir", ""))
        self.template_path = tk.StringVar(value=settings.get("template_path", ""))
        self.result: tuple[str, str, str] | None = None

        # Main container
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Grid configuration
        main_frame.columnconfigure(1, weight=1)

        # CSV Selection
        ttk.Label(main_frame, text="CSV File:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.csv_path).grid(row=0, column=1, sticky="we", padx=5, pady=5)
        ttk.Button(main_frame, text="Browse...", command=self.browse_csv).grid(row=0, column=2, pady=5, padx=5)

        # Audio Dir Selection
        ttk.Label(main_frame, text="Audio Directory:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.audio_dir).grid(row=1, column=1, sticky="we", padx=5, pady=5)
        ttk.Button(main_frame, text="Browse...", command=self.browse_audio).grid(row=1, column=2, pady=5, padx=5)

        # Template Path
        ttk.Label(main_frame, text="Template Event Path:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.template_path).grid(row=2, column=1, columnspan=2, sticky="we", padx=5, pady=5)

        # Separator
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).grid(row=3, column=0, columnspan=3, sticky="we", pady=15)

        # Rules Summary
        rules_frame = ttk.LabelFrame(main_frame, text="Defaulting Rules", padding="10")
        rules_frame.grid(row=4, column=0, columnspan=3, sticky="wens", pady=5)

        rules_text = (
            "1. Event Path: Derived from CSV 'event_path' column.\n"
            "2. Audio File: Derived from CSV 'audio_path' column.\n"
            "3. Template: Used if specified, otherwise defaults to basic event creation.\n"
            "4. Bus/Bank: Looked up by name; skipped if not found."
        )
        ttk.Label(rules_frame, text=rules_text, justify=tk.LEFT).pack(anchor=tk.W)

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=5, column=0, columnspan=3, pady=20)
        ttk.Button(btn_frame, text="Run Import", command=self.run_import).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Cancel", command=self.cancel).pack(side=tk.LEFT, padx=10)

        # Center window
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

        self.root.deiconify()

    def browse_csv(self) -> None:
        f = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if f:
            self.csv_path.set(f)

    def browse_audio(self) -> None:
        d = filedialog.askdirectory()
        if d:
            self.audio_dir.set(d)

    def run_import(self) -> None:
        if not self.csv_path.get() or not self.audio_dir.get():
            messagebox.showerror("Error", "Please select both CSV file and Audio directory.")
            return
        _save_settings({
            "csv_path": self.csv_path.get(),
            "audio_dir": self.audio_dir.get(),
            "template_path": self.template_path.get(),
        })
        self.result = (self.csv_path.get(), self.audio_dir.get(), self.template_path.get())
        self.root.destroy()

    def cancel(self) -> None:
        self.root.destroy()


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


def run_selection_flow() -> tuple[str | None, str | None, str | None]:
    """
    Run the full GUI selection flow.
    Returns (csv_path, audio_dir, template_path) or (None, None, None) if cancelled.
    """
    if TEST_MODE == "cancel":
        return None, None, None
    if TEST_MODE:
        return FIXTURE_CSV, FIXTURE_AUDIO_DIR, ""

    root = tk.Tk()
    app = BatchImportDialog(root)
    root.mainloop()

    if app.result:
        return app.result
    return None, None, None
