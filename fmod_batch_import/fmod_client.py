import socket


class FMODConnectionError(Exception):
    """Raised when FMOD TCP connection is lost or unavailable."""


class FMODClient:
    def __init__(self, host: str = "localhost", port: int = 3663):
        self.host: str = host
        self.port: int = port
        self._socket: socket.socket | None = None

    def connect(self) -> bool:
        try:
            self._socket = socket.create_connection((self.host, self.port))
            return True
        except ConnectionRefusedError:
            self._socket = None
            return False

    def execute(self, js_code: str) -> str:
        """Execute JS code via FMOD TCP scripting API.

        Raises:
            FMODConnectionError: If connection cannot be established or is lost.
        """
        if self._socket is None:
            if not self.connect():
                raise FMODConnectionError(
                    f"Cannot connect to FMOD Studio at {self.host}:{self.port}"
                )
        sock = self._socket
        assert sock is not None  # guaranteed by connect() above
        try:
            sock.settimeout(30.0)
            sock.sendall(js_code.encode("utf-8"))
            chunks = []
            while True:
                try:
                    chunk = sock.recv(4096)
                except socket.timeout:
                    break
                if not chunk:
                    break
                chunks.append(chunk)
                # Stop only when a complete out(): packet has arrived.
                # FMOD may emit multiple log(): packets before out():; counting
                # null bytes would stop too early and lose the JSON response.
                current = b"".join(chunks)
                out_idx = current.find(b"out():")
                if out_idx != -1 and b"\x00" in current[out_idx:]:
                    break
            sock.settimeout(None)
            response = b''.join(chunks)
            return response.decode("utf-8")
        except ConnectionRefusedError as exc:
            self._socket = None
            raise FMODConnectionError("FMOD connection refused during execute") from exc
        except socket.timeout as exc:
            raise FMODConnectionError("FMOD connection timed out") from exc
        except OSError as exc:
            self._socket = None
            raise FMODConnectionError(f"FMOD socket error: {exc}") from exc

    def close(self) -> None:
        if self._socket is not None:
            self._socket.close()
            self._socket = None
