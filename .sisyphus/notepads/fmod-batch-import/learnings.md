
## FMODClient Tests

Created `tests/test_fmod_client.py` with mocked socket tests:

1. **test_connect_success** - Verifies `socket.create_connection` succeeds and returns True
2. **test_connect_failure** - Verifies `ConnectionRefusedError` handling returns False  
3. **test_execute_sends_js** - Verifies `sendall` called with UTF-8 encoded JS code
4. **test_execute_receives_response** - Verifies response decoded from UTF-8 bytes
5. **test_execute_auto_connects** - Execute without prior connect auto-connects
6. **test_close_closes_socket** - Verifies `socket.close()` called and reference cleared

All tests use `@patch("socket.create_connection")` to mock the socket layer.
