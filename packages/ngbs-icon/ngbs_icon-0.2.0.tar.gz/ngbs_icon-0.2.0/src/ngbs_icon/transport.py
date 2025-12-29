from __future__ import annotations

import asyncio
import json
from typing import Any

import async_timeout

from .exceptions import TransportError


class Transport:
    """Low-level transport for NGBS iCON.

    This class is responsible for all I/O.
    No business logic, no data interpretation.
    """

    def __init__(self, host: str, port: int = 7992, timeout: float = 2.0):
        self._host = host
        self._port = port
        self._timeout = timeout

    async def request(self, payload: dict[str, Any]) -> dict[str, Any]:
        writer = None
        try:
            async with async_timeout.timeout(self._timeout):
                reader, writer = await asyncio.open_connection(self._host, self._port)

                writer.write(json.dumps(payload).encode())
                await writer.drain()

                try:
                    writer.write_eof()
                except Exception:
                    pass

                raw = await reader.read()

            if not raw:
                raise TransportError("Empty response from controller")

            try:
                data = json.loads(raw.decode())
            except json.JSONDecodeError as err:
                raise TransportError(f"Invalid JSON response: {raw!r}") from err

            return data

        except Exception as err:
            raise TransportError(str(err)) from err

        finally:
            if writer is not None:
                writer.close()
                await writer.wait_closed()
