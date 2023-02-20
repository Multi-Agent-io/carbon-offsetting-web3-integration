"""Config flow for Web3 Carbon Footprint Offsetting Integration."""

from __future__ import annotations

import logging
from typing import Any, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import selector
from robonomicsinterface import Account

from .const import (
    CONF_ADMIN_SEED,
    CONF_ENERGY_CONSUMPTION_ENTITIES,
    CONF_ENERGY_PRODUCTION_ENTITIES,
    CONF_IPFS_GATEWAY_AUTH,
    CONF_IPFS_GATEWAY_PWD,
    CONF_IPFS_GW,
    CONF_IS_W3GW,
    CONF_WARN_DATA_SENDING,
    DOMAIN,
)
from .exceptions import InvalidIPFSCreds, InvalidSeed

_LOGGER = logging.getLogger(__name__)

STEP_CONF_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ENERGY_CONSUMPTION_ENTITIES): selector(
            {"entity": {"multiple": True, "device_class": "energy"}}
        ),
        vol.Required(CONF_ENERGY_PRODUCTION_ENTITIES): selector(
            {"entity": {"multiple": True, "device_class": "energy"}}
        ),
        vol.Required(CONF_ADMIN_SEED): str,
        vol.Optional(CONF_IPFS_GW): str,
        vol.Optional(CONF_IS_W3GW): bool,
        vol.Optional(CONF_IPFS_GATEWAY_AUTH): str,
        vol.Optional(CONF_IPFS_GATEWAY_PWD): str,
    }
)

STEP_WARN_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_WARN_DATA_SENDING): bool,
    }
)


def is_valid_sub_admin_seed(sub_admin_seed: str) -> Optional[ValueError]:
    """
    Check whether supplied seed is correct.

    :param sub_admin_seed: HomeAssistant user's Robonomics Account seed in any form.

    :return: Optional error.

    """
    try:
        Account(sub_admin_seed)
    except Exception as e:
        return e


def is_valid_ipfs_creds(data: dict) -> bool:
    """
    Check whether supplied IPFS credentials are correct.

    :param data: User input.

    :return: Whether provided data meets required logic.

    """
    if CONF_IS_W3GW in data and (CONF_IPFS_GATEWAY_AUTH in data or CONF_IPFS_GATEWAY_PWD in data):
        return False
    if CONF_IPFS_GATEWAY_AUTH in data and CONF_IPFS_GATEWAY_PWD not in data:
        return False
    if CONF_IPFS_GATEWAY_PWD in data and CONF_IPFS_GATEWAY_AUTH not in data:
        return False
    return True


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """
    Validate the user input allows us to connect. Data has the keys from STEP_USER_DATA_SCHEMA with values provided
        by the user.

    :param hass: HomeAssistant instance.
    :param data: User input.

    :return: Integration setup title.

    """
    if await hass.async_add_executor_job(is_valid_sub_admin_seed, data[CONF_ADMIN_SEED]):
        raise InvalidSeed
    if not await hass.async_add_executor_job(is_valid_ipfs_creds, data):
        raise InvalidIPFSCreds

    return {"title": "CO2 Offsetting Web3"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Web3 Carbon Offsetting Integration."""

    # The schema version of the entries that it creates
    # Home Assistant will call your migrate method if the version changes
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """
        User step of integration installation. Shows warnings.

        :param user_input: User input.

        :return: Setup entry from ``async_step_conf``

        """

        errors = {}
        device_unique_id = "co2_offsetting_web3"
        await self.async_set_unique_id(device_unique_id)
        self._abort_if_unique_id_configured()
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=STEP_WARN_DATA_SCHEMA)
        else:
            if [x for x in user_input if not user_input[x]]:
                errors["base"] = "warnings"
                return self.async_show_form(step_id="user", data_schema=STEP_WARN_DATA_SCHEMA, errors=errors)
            return await self.async_step_conf()

    async def async_step_conf(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """
        Configuration step of integration installation. Shows input form to pick entities and set Robonomics and IPFS
            creds.

        :param user_input: User input.

        :return: Setup entry.

        """
        if user_input is None:
            return self.async_show_form(step_id="conf", data_schema=STEP_CONF_DATA_SCHEMA)

        errors = {}

        try:
            info = await validate_input(self.hass, user_input)
        except InvalidSeed:
            errors["base"] = "invalid_seed"
            _LOGGER.exception("invalid_seed")
        except InvalidIPFSCreds:
            errors["base"] = "invalid_ipfs_creds"
            _LOGGER.exception("invalid_ipfs_creds")
        else:
            return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(step_id="conf", data_schema=STEP_CONF_DATA_SCHEMA, errors=errors)
