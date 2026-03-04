#!/usr/bin/env python3
"""Verify FMOD TCP connection and basic execution."""

import json
import sys
from typing import Any

try:
    from fmod_batch_import.fmod_client import FMODClient
except ImportError as e:
    print(json.dumps({
        "connected": False,
        "exec_ok": False,
        "result": None,
        "error": f"Failed to import FMODClient: {e}"
    }))
    sys.exit(1)

def main() -> int:
    client: FMODClient | None = None
    connected = False
    exec_ok = False
    result: Any = None
    error: str | None = None

    try:
        client = FMODClient(host="localhost", port=3663)
        connected = client.connect()

        if not connected:
            error = "Failed to connect to FMOD Studio at localhost:3663"
        else:
            try:
                exec_result = client.execute("studio.project.workspace.entity")
                exec_ok = True
                # Convert result to string representation for JSON serialization
                result = str(exec_result) if exec_result is not None else None
            except Exception as e:
                exec_ok = False
                error = f"Execution failed: {e}"

    except Exception as e:
        if not connected:
            error = f"Connection error: {e}"
        else:
            error = f"Unexpected error: {e}"

    finally:
        if client is not None:
            try:
            try:
                client.disconnect()
            except Exception:
                pass
            except Exception:
                pass

    output = {
        "connected": connected,
        "exec_ok": exec_ok,
        "result": result,
        "error": error
    }

    print(json.dumps(output, indent=2))
    return 0 if (connected and exec_ok) else 1

if __name__ == "__main__":
    sys.exit(main())
