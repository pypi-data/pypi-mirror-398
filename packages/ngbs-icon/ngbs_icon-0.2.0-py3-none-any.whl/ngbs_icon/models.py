from __future__ import annotations
from typing import Dict, Any


class IconZone:
    """
    Class that represents a single DP (zone / thermostat) entry of the iCON controller.
    """

    def __init__(self, zone_id: str, raw_data: Dict[str, Any], transport) -> None:
        self.zone_id = zone_id
        self.raw_data = raw_data
        self._transport = transport

    @property
    def NAME(self):
        """Zone name."""
        return self.raw_data.get("NAME")

    # ---- State ----
    
    @property
    def ON(self):
        """Zone enabled (1 = enabled)."""
        return self.raw_data.get("ON")

    @property
    def LIVE(self):
        """Zone live / reporting."""
        return self.raw_data.get("LIVE")

    # ---- Environmental Readings ----

    @property
    def TEMP(self):
        """Measured room temperature (°C)."""
        return self.raw_data.get("TEMP")

    @property
    def RH(self):
        """Relative humidity (%)."""
        return self.raw_data.get("RH")

    @property
    def DEW(self):
        """Dew point temperature (°C)."""
        return self.raw_data.get("DEW")

    # ---- Target Values ----

    @property
    def XAH(self):
        """Comfort heating target."""
        return self.raw_data.get("XAH")

    @property
    def XAC(self):
        """Comfort cooling target."""
        return self.raw_data.get("XAC")

    @property
    def ECOH(self):
        """Eco heating target."""
        return self.raw_data.get("ECOH")

    @property
    def ECOC(self):
        """Eco cooling target."""
        return self.raw_data.get("ECOC")

    # ---- Modes ----

    @property
    def CE(self):
        """Eco mode active (1 = eco)."""
        return self.raw_data.get("CE")

    @property
    def HC(self):
        """Heating/Cooling mode (1 = cooling)."""
        return self.raw_data.get("HC")

    # ---- Misc ----
    
    @property
    def CEF(self):
        """Eco follows master controller eco mode."""
        return self.raw_data.get("CEF")

    @property
    def DXH(self):
        """Floor heating offset."""
        return self.raw_data.get("DXH")

    @property
    def DXC(self):
        """Floor cooling offset."""
        return self.raw_data.get("DXC")

    @property
    def LIM(self):
        """Adjustment limit (+/- °C around midpoint)."""
        return self.raw_data.get("LIM")
    
    @property
    def CEC(self):
        """Eco cooling capability flag."""
        return self.raw_data.get("CEC")

    @property
    def DI(self):
        """Digital input state."""
        return self.raw_data.get("DI")

    @property
    def OUT(self):
        """Valve output state."""
        return self.raw_data.get("OUT")

    @property
    def PL(self):
        """Parental lock (1 = locked)."""
        return self.raw_data.get("PL")

    @property
    def MV(self):
        """Mixing valve presence/state."""
        return self.raw_data.get("MV")

    @property
    def WP(self):
        """Window protection enabled."""
        return self.raw_data.get("WP")

    @property
    def DWP(self):
        """Dew point protection active."""
        return self.raw_data.get("DWP")

    @property
    def FROST(self):
        """Frost protection active."""
        return self.raw_data.get("FROST")

    @property
    def TPR(self):
        """Time program active."""
        return self.raw_data.get("TPR")

    # ---- Write operations ----

    async def async_set_XAH(self, sysid: str, value):
        """Set comfort heating target for the room."""
        await self._transport.request({"SYSID": sysid, "DP": {self.zone_id: {"XAH": value}}})

    async def async_set_XAC(self, sysid: str, value):
        """Set comfort cooling target for the room."""
        await self._transport.request({"SYSID": sysid, "DP": {self.zone_id: {"XAC": value}}})

    async def async_set_ECOH(self, sysid: str, value):
        """Set eco heating target for the room."""
        await self._transport.request({"SYSID": sysid, "DP": {self.zone_id: {"ECOH": value}}})

    async def async_set_ECOC(self, sysid: str, value):
        """Set eco cooling target for the room."""
        await self._transport.request({"SYSID": sysid, "DP": {self.zone_id: {"ECOC": value}}})

    async def async_set_CE(self, sysid: str, value: int):
        """Enable/disable eco mode for this zone(1 = eco)."""
        await self._transport.request({"SYSID": sysid, "DP": {self.zone_id: {"CE": value}}})

    async def async_set_HC(self, sysid: str, value: int):
        """Set heating/cooling mode for this zone(1 = cooling)."""
        await self._transport.request({"SYSID": sysid, "DP": {self.zone_id: {"HC": value}}})


class IconInfo:
    """
    Class that represents the INFO block of the iCON controller.
    """

    def __init__(self, raw_data: Dict[str, Any]) -> None:
        self.raw_data = raw_data or {}

    @property
    def FIRMWARE(self):
        """Firmware build number."""
        return self.raw_data.get("FIRMWARE")

    @property
    def UPTIME(self):
        """Controller uptime."""
        return self.raw_data.get("UPTIME")

    @property
    def TASK(self):
        """Active controller tasks."""
        return self.raw_data.get("TASK")

    @property
    def NETL(self):
        """Network interfaces mapping."""
        return self.raw_data.get("NETL")


class IconController:
    """
    Class that represents an NGBS iCON controller.
    """

    def __init__(self, sysid: str, raw_data: Dict[str, Any], transport) -> None:
        self.SYSID = sysid
        self.raw_data = raw_data
        self._transport = transport

        self.zones: Dict[str, "IconZone"] = {}
        self._parse_zones()

    # ---- Metadata ----
    @property
    def VER(self):
        """Firmware version string."""
        return self.raw_data.get("VER")

    @property
    def INFO(self) -> IconInfo:
        """Controller info block."""
        return IconInfo(self.raw_data.get("INFO"))

    @property
    def TZ(self):
        """Controller timezone."""
        return self.raw_data.get("TZ")

    @property
    def EMAIL(self):
        """Configured service email address."""
        return self.raw_data.get("EMAIL")

    # ---- Global operating state ----
    @property
    def ON(self):
        """Controller enabled state."""
        return self.raw_data.get("ON")

    @property
    def SERVICE(self):
        """Service / maintenance mode active."""
        return self.raw_data.get("SERVICE")

    @property
    def CE(self):
        """Eco mode active on controller level."""
        return self.raw_data.get("CE")

    @property
    def HC(self):
        """Heating / cooling selector (raw value)."""
        return self.raw_data.get("HC")

    # ---- Global Environmental Variables ----
    @property
    def ETEMP(self):
        """External temperature (°C)."""
        return self.raw_data.get("ETEMP")

    @property
    def WTEMP(self):
        """Water temperature (°C)."""
        return self.raw_data.get("WTEMP")

    # ---- Global Targets ----
    @property
    def XAH(self):
        """Global comfort heating target."""
        return self.raw_data.get("XAH")

    @property
    def XAC(self):
        """Global comfort cooling target."""
        return self.raw_data.get("XAC")

    @property
    def ECOH(self):
        """Global eco heating target."""
        return self.raw_data.get("ECOH")

    @property
    def ECOC(self):
        """Global eco cooling target."""
        return self.raw_data.get("ECOC")

    # ---- Misc ----
    @property
    def PUMP(self):
        """Pump active state."""
        return self.raw_data.get("PUMP")

    @property
    def OVERHEAT(self):
        """Overheat protection active."""
        return self.raw_data.get("OVERHEAT")

    @property
    def WFROST(self):
        """Water frost protection active."""
        return self.raw_data.get("WFROST")

    @property
    def SIG(self):
        """Signal / alarm state."""
        return self.raw_data.get("SIG")

    @property
    def SW(self):
        """Service switch state."""
        return self.raw_data.get("SW")

    @property
    def TPR(self):
        """Time program definitions.

        Contains HEAT / COOL program structures.
        """
        return self.raw_data.get("TPR")

    # ---- Write operations ----
    async def async_set_CE(self, value: int) -> None:
        """Enable or disable eco mode on controller level."""
        await self._transport.request(
            {
                "SYSID": self.SYSID,
                "CE": value,
            }
        )

    async def async_set_HC(self, value: int) -> None:
        """Set heating / cooling mode."""
        await self._transport.request(
            {
                "SYSID": self.SYSID,
                "HC": value,
            }
        )

    async def async_set_XAH(self, value) -> None:
        """Set global comfort heating target."""
        await self._transport.request(
            {
                "SYSID": self.SYSID,
                "XAH": value,
            }
        )

    async def async_set_XAC(self, value) -> None:
        """Set global comfort cooling target."""
        await self._transport.request(
            {
                "SYSID": self.SYSID,
                "XAC": value,
            }
        )

    async def async_set_ECOH(self, value) -> None:
        """Set global eco heating target."""
        await self._transport.request(
            {
                "SYSID": self.SYSID,
                "ECOH": value,
            }
        )

    async def async_set_ECOC(self, value) -> None:
        """Set global eco cooling target."""
        await self._transport.request(
            {
                "SYSID": self.SYSID,
                "ECOC": value,
            }
        )

    # ----Update ----
    async def async_update(self) -> None:
        """Refresh controller and zone data from device."""
        self.raw_data = await self._transport.request(
            {"SYSID": self.SYSID}
        )
        self._parse_zones()
        
    # ---- Parsing ----
    def _parse_zones(self) -> None:
        """Parse DP entries into zone objects."""
        from .models import IconZone

        self.zones.clear()
        for zone_id, zone_data in self.raw_data.get("DP", {}).items():
            self.zones[zone_id] = IconZone(
                zone_id=zone_id,
                raw_data=zone_data,
                transport=self._transport,
            )