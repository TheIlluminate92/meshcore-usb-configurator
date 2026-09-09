"""Exercise the actual async serial transport without a physical radio."""
import asyncio
import time
import unittest
import serial
from serial_asyncio_fast import connection_for_serial
from serial_connection import ClosingSerialConnection


class Cleanup(unittest.TestCase):
    def test_repeated_operations_release_handle_before_loop_shutdown(self):
        for _ in range(3):
            handle = serial.serial_for_url('loop://', timeout=0)
            # Force the real transport to await an executor flush, exposing
            # the race between disconnect returning and loop shutdown.
            original_flush = handle.flush
            def slow_flush():
                time.sleep(.04)
                original_flush()
            handle.flush = slow_flush
            async def operation():
                connection = ClosingSerialConnection('loop://', 115200)
                await connection_for_serial(asyncio.get_running_loop(),
                                            lambda: connection.MCSerialClientProtocol(connection), handle)
                await connection._connected_event.wait()
                await connection.disconnect()
                self.assertTrue(connection.closed.is_set())
                self.assertFalse(handle.is_open)
                await connection.disconnect()  # cleanup is idempotent
            try:
                asyncio.run(operation())
                self.assertFalse(handle.is_open)
            finally:
                handle.close()

if __name__ == '__main__':
    unittest.main()
