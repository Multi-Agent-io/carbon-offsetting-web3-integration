"""Platform for offsetting client integration."""

import logging

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.const import DEVICE_CLASS_ENERGY, ENERGY_KILO_WATT_HOUR

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add sensors for passed config_entry in HA."""
    _LOGGER.debug("Start sensors setup")
    client = hass.data[DOMAIN][config_entry.entry_id]
    new_devices = [ToCompensate(client), LastCompensationDate(client), TotalCompensated(client)]
    if new_devices:
        async_add_entities(new_devices)


class SensorBase(SensorEntity):
    should_poll = False

    def __init__(self, client):
        """Initialize the sensor."""
        self._client = client

    @property
    def device_info(self):
        """Return information to link this entity with the correct device."""
        return {
            "identifiers": {(DOMAIN, self._client.client_id)},
            "name": self._client.name,
            "sw_version": self._client.sw_version,
            "model": self._client.model,
            "manufacturer": self._client.manufacturer,
        }

    @property
    def available(self) -> bool:
        """Return True if client and hub are available."""
        return True

    async def async_added_to_hass(self):
        """Run when this Entity has been added to HA."""
        self._client.register_callback(self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        """Entity being removed from hass."""
        self._client.remove_callback(self.async_write_ha_state)


class ToCompensate(SensorBase):
    def __init__(self, client):
        """Initialize the sensor."""
        super().__init__(client)
        _LOGGER.debug(f"Initiating ToCompensate")

        self._attr_unique_id = f"{self._client._id}_to_compensate"

        # The name of the entity
        self._attr_name = f"To compensate"
        self.entity_description = SensorEntityDescription(
            key="setpoint",
            name=self._attr_name,
            native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
            device_class=DEVICE_CLASS_ENERGY,
            state_class=SensorStateClass.MEASUREMENT,
            icon="mdi:leaf-circle-outline",
        )
        self._state = 0

    @property
    def state(self):
        """Return the state of the sensor."""

        return self._client.to_compensate


class LastCompensationDate(SensorBase):
    def __init__(self, client):
        """Initialize the sensor."""
        super().__init__(client)
        _LOGGER.debug(f"Initiating LastCompensationDate")

        self._attr_unique_id = f"{self._client._id}_last_compensation_date"

        # The name of the entity
        self._attr_name = f"Last compensation date"
        self.entity_description = SensorEntityDescription(key="setpoint", name=self._attr_name, icon="mdi:calendar")
        self._state = "-"

    @property
    def state(self):
        """Return the state of the sensor."""

        return self._client.last_compensation_date


class TotalCompensated(SensorBase):
    def __init__(self, client):
        """Initialize the sensor."""
        super().__init__(client)
        _LOGGER.debug(f"Initiating TotalCompensated")

        self._attr_unique_id = f"{self._client._id}_total_compensated"

        # The name of the entity
        self._attr_name = f"Total compensated"
        self.entity_description = SensorEntityDescription(
            key="setpoint",
            name=self._attr_name,
            native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
            device_class=DEVICE_CLASS_ENERGY,
            state_class=SensorStateClass.MEASUREMENT,
            icon="mdi:leaf-circle",
        )
        self._state = 0

    @property
    def state(self):
        """Return the state of the sensor."""

        return self._client.total_compensated
