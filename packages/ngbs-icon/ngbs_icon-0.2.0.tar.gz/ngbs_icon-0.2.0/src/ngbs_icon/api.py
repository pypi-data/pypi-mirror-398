from __future__ import annotations

from typing import Optional

from .transport import Transport
from .models import IconController

from .exceptions import ProtocolError

class NgbsIconApi:
    """
    Class to communicate with the NGBS iCON API.
    """

    def __init__(self, host: str, port: int = 7992, *, timeout: float = 3.0) -> None:
        self._transport = Transport(host, port, timeout=timeout)
        self._controller: Optional[IconController] = None

    async def async_get_controller(self, sysid: str) -> IconController:
        """Fetch controller state and return an IconController model."""
        raw = await self._transport.request({"SYSID": sysid})

        self._controller = IconController(
            sysid=sysid,
            raw_data=raw,
            transport=self._transport,
        )
        return self._controller

    async def async_refresh(self) -> IconController:
        """Refresh the last fetched controller."""
        if self._controller is None:
            raise RuntimeError("Controller not initialized")

        await self._controller.async_update()
        return self._controller
    
    async def async_get_sysid(self) -> str:
        """Ask the controller for its SYSID."""
        try:
            raw = await self._transport.request({"RELOAD": 6})
        except ProtocolError as e:
            raise ProtocolError("Failed to retrieve SYSID.", response=str(e))

        sysid = raw.get("SYSID")
        if not sysid:
            raise ProtocolError("No SYSID found in controller response", response=str(raw))

        return sysid