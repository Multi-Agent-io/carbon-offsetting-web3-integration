"""A demonstration 'hub' that connects several devices."""
from __future__ import annotations


import asyncio

from homeassistant.core import HomeAssistant
import logging
_LOGGER = logging.getLogger(__name__)


class Client:
    """Offsetting Client class."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Init."""
        _LOGGER.debug(f"Initiating Client")
        self.name = "Carbon Offsetting Client"
        self._id = "carbon_offsetting"
        self.sw_version = "0.0.1"
        self.model = "Carbon Offsetting Client"
        self.manufacturer = "Robonomics"

        self._hass = hass
        self._callbacks = set()
        self._loop = asyncio.get_event_loop()

        self._to_compensate = "Yet unknown"
        self._last_compensation_date = "Yet unknown"
        self._total_compensated = "Yet unknown"

    @property
    def client_id(self) -> str:
        """Return ID for client."""
        return self._id

    @property
    def to_compensate(self) -> float | str:
        """Amount of kWh to compensate."""
        return self._to_compensate

    def set_to_compensate(self, val):
        """Set amount of kWh to compensate."""
        self._to_compensate = val

    @property
    def last_compensation_date(self) -> str:
        """Last compensation date."""
        return self._last_compensation_date

    def set_last_compensation_date(self, val):
        """Set last compensation date."""
        self._last_compensation_date = val

    @property
    def total_compensated(self) -> float | str:
        """Amount of kWh total compensated."""
        return self._total_compensated

    def set_total_compensated(self, val):
        """Set amount of kWh total compensated."""
        self._total_compensated = val
    
    @property
    def online(self) -> float:
        """Client is online."""
        return True

    def register_callback(self, callback) -> None:
        """Register callback, called when Client changes state."""
        self._callbacks.add(callback)

    def remove_callback(self, callback) -> None:
        """Remove previously registered callback."""
        self._callbacks.discard(callback)

    def publish_updates(self) -> None:
        """Schedule call all registered callbacks."""
        for callback in self._callbacks:
            callback()

    async def test_connection(self) -> bool:
        """Test connectivity to the Client hub is OK."""
        await asyncio.sleep(1)
        return True
