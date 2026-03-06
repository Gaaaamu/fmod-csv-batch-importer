"""
Entry point for FMOD Batch Import.

Usage:
    python -m fmod_batch_import        # GUI mode (double-click .bat)
    FMOD_IMPORTER_TEST_MODE=1 python -m fmod_batch_import  # Test mode
"""

import sys

from fmod_batch_import.gui import run_selection_flow, show_error, show_info, prompt_start_fmod
from fmod_batch_import.fmod_client import FMODClient, FMODConnectionError
from fmod_batch_import.orchestrator import Orchestrator


def main() -> int:
    # --- Step 1: Get CSV and audio directory via GUI ---
    csv_path, audio_dir, template_path = run_selection_flow()
    if not csv_path or not audio_dir:
        return 0  # User cancelled cleanly

    # --- Step 2: Connect to FMOD ---
    client = FMODClient()
    max_retries = 3
    connected = False

    for attempt in range(max_retries):
        if client.connect():
            connected = True
            break
        # Prompt user to start FMOD
        if not prompt_start_fmod():
            show_error("Connection Failed", "Could not connect to FMOD Studio. Aborting.")
            return 1

    if not connected:
        show_error(
            "Connection Failed",
            "Could not connect to FMOD Studio after multiple attempts.\n"
            "Please ensure FMOD Studio is open and the scripting server is enabled.",
        )
        return 1

    # --- Step 3: Run batch import ---
    try:
        orch = Orchestrator(csv_path, audio_dir, client, template_event_path=template_path)
        summary = orch.run()

        show_info(
            "Import Complete",
            f"Batch import finished.\n\n"
            f"  Total:   {summary.total}\n"
            f"  Success: {summary.success}\n"
            f"  Skipped: {summary.skip}\n"
            f"  Failed:  {summary.fail}\n\n"
            f"Log written to CSV directory.",
        )
        return 0 if summary.fail == 0 else 1

    except FMODConnectionError as exc:
        show_error("FMOD Connection Lost", f"Connection to FMOD was lost during import:\n{exc}")
        return 1
    except ValueError as exc:
        show_error("Import Error", str(exc))
        return 1
    except Exception as exc:
        show_error("Unexpected Error", str(exc))
        return 1
    finally:
        client.close()


if __name__ == "__main__":
    sys.exit(main())
