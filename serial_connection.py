"""Wait for the Windows handle to close before an operation's loop exits."""
import asyncio
from meshcore import SerialConnection


class ClosingSerialConnection(SerialConnection):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.closed = asyncio.Event()

    class MCSerialClientProtocol(SerialConnection.MCSerialClientProtocol):
        def connection_made(self, transport):
            self.cx.closed.clear()
            super().connection_made(transport)

        def connection_lost(self, exc):
            try:
                super().connection_lost(exc)
            finally:
                self.cx.closed.set()

    async def disconnect(self):
        transport = self.transport
        if transport is None:
            return
        handle = transport.serial
        await super().disconnect()
        try:
            # The transport flushes and closes in executor tasks. Returning
            # before connection_lost lets asyncio.run cancel those tasks.
            await asyncio.wait_for(self.closed.wait(), timeout=5)
        finally:
            if handle is not None and handle.is_open:
                await asyncio.to_thread(handle.close)
