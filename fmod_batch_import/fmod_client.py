import socket


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

    def execute(self, js_code: str) -> str | None:
        if self._socket is None:
            if not self.connect():
                return None
        if self._socket is None:
            return None
        try:
            self._socket.settimeout(10.0)
            self._socket.sendall(js_code.encode("utf-8"))
            chunks = []
            total_nulls = 0
            while True:
                try:
                    chunk = self._socket.recv(4096)
                except socket.timeout:
                    break
                if not chunk:
                    break
                chunks.append(chunk)
                total_nulls += chunk.count(b'\0')
                if total_nulls >= 2:
                    break
            self._socket.settimeout(None)
            response = b''.join(chunks)
            return response.decode("utf-8")
        except (ConnectionRefusedError, socket.timeout):
            return None

    def close(self) -> None:
        if self._socket is not None:
            self._socket.close()
            self._socket = None
