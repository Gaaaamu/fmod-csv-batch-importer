import socket
import unittest
from unittest.mock import patch, MagicMock

from fmod_batch_import.fmod_client import FMODClient


class TestFMODClient(unittest.TestCase):
    def setUp(self):
        self.client = FMODClient(host="localhost", port=3663)

    @patch("socket.create_connection")
    def test_connect_success(self, mock_create_connection):
        """Test that connect returns True when socket.create_connection succeeds."""
        mock_socket = MagicMock()
        mock_create_connection.return_value = mock_socket

        result = self.client.connect()

        self.assertTrue(result)
        mock_create_connection.assert_called_once_with(("localhost", 3663))
        self.assertEqual(self.client._socket, mock_socket)

    @patch("socket.create_connection")
    def test_connect_failure(self, mock_create_connection):
        """Test that connect returns False when socket.create_connection raises ConnectionRefusedError."""
        mock_create_connection.side_effect = ConnectionRefusedError()

        result = self.client.connect()

        self.assertFalse(result)
        mock_create_connection.assert_called_once_with(("localhost", 3663))
        self.assertIsNone(self.client._socket)

    @patch("socket.create_connection")
    def test_execute_sends_js(self, mock_create_connection):
        """Test that execute sends JS code as UTF-8 encoded bytes via sendall."""
        mock_socket = MagicMock()
        mock_create_connection.return_value = mock_socket
        mock_socket.recv.side_effect = [b"log\0out(): ok\0"]

        self.client.connect()
        js_code = 'studio.project.create("Event", "test_event")'
        self.client.execute(js_code)

        mock_socket.sendall.assert_called_once_with(js_code.encode("utf-8"))

    @patch("socket.create_connection")
    def test_execute_receives_response(self, mock_create_connection):
        """Test that execute receives and decodes response from UTF-8 bytes."""
        mock_socket = MagicMock()
        mock_create_connection.return_value = mock_socket
        mock_socket.recv.side_effect = [b"log(): event created\0out(): ok\0"]

        self.client.connect()
        result = self.client.execute('studio.project.create("Event")')

        self.assertEqual(result, "log(): event created\x00out(): ok\x00")
        mock_socket.recv.assert_called_with(4096)

    @patch("socket.create_connection")
    def test_execute_auto_connects(self, mock_create_connection):
        """Test that execute auto-connects when called without prior connect."""
        mock_socket = MagicMock()
        mock_create_connection.return_value = mock_socket
        mock_socket.recv.side_effect = [b"log\0out(): ok\0"]

        # Execute without calling connect first
        result = self.client.execute('studio.project.create("Event")')

        # Should have auto-connected
        mock_create_connection.assert_called_once_with(("localhost", 3663))
        self.assertIsNotNone(result)

    @patch("socket.create_connection")
    def test_execute_multiple_log_lines_before_out(self, mock_create_connection):
        """Multiple log(): packets before out(): must not cause early termination.

        This guards against the bug where total_nulls >= 2 fires on the second
        log() packet, stopping the read loop before out(): is received.
        """
        mock_socket = MagicMock()
        mock_create_connection.return_value = mock_socket
        # FMOD emits 3 log() messages then the out() JSON — all in one recv chunk
        payload = (
            b"log(): importing audio\x00"
            b"log(): creating event\x00"
            b"log(): assigning bank\x00"
            b'out(): {"ok":true,"results":[]}\x00'
        )
        mock_socket.recv.side_effect = [payload, socket.timeout()]

        self.client.connect()
        result = self.client.execute("js_code")

        self.assertIn("out():", result)
        self.assertIn('"ok":true', result)

    @patch("socket.create_connection")
    def test_execute_out_arrives_in_later_chunk(self, mock_create_connection):
        """out(): arriving in a later recv chunk is still collected correctly."""
        mock_socket = MagicMock()
        mock_create_connection.return_value = mock_socket
        # First chunk: two log() packets; second chunk: the out() packet
        mock_socket.recv.side_effect = [
            b"log(): msg1\x00log(): msg2\x00",
            b'out(): {"ok":true}\x00',
            socket.timeout(),
        ]

        self.client.connect()
        result = self.client.execute("js_code")

        self.assertIn("out():", result)
        self.assertIn('"ok":true', result)

    @patch("socket.create_connection")
    def test_execute_timeout_without_out_returns_partial(self, mock_create_connection):
        """If out(): never arrives, the read loop exits on timeout with partial data."""
        mock_socket = MagicMock()
        mock_create_connection.return_value = mock_socket
        mock_socket.recv.side_effect = [b"log(): something\x00", socket.timeout()]

        self.client.connect()
        result = self.client.execute("js_code")

        # Partial response — no out(): present
        self.assertNotIn("out():", result)
        self.assertIn("log(): something", result)

    @patch("socket.create_connection")
    def test_close_closes_socket(self, mock_create_connection):
        """Test that close calls socket.close() and clears the socket reference."""
        mock_socket = MagicMock()
        mock_create_connection.return_value = mock_socket

        self.client.connect()
        self.client.close()

        mock_socket.close.assert_called_once()
        self.assertIsNone(self.client._socket)


if __name__ == "__main__":
    unittest.main()
