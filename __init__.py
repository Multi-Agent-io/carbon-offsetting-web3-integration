"""Web3 Carbon Footprint Offsetting Integration."""
import asyncio
import logging
from datetime import date

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from robonomicsinterface import Account, Liability, web_3_auth
from substrateinterface import KeypairType

from .client import Client
from .const import (CONF_ADMIN_SEED, CONF_IPFS_GATEWAY_AUTH,
                    CONF_IPFS_GATEWAY_PWD, CONF_IPFS_GW, CONF_IS_W3GW, DOMAIN,
                    IPFS_GW, LAST_COMPENSATION_DATE_RESPONSE_TOPIC,
                    LIABILITY_REPORT_TOPIC)
from .utils.offsetting_client import (send_last_compensation_date_query,
                                      send_offset_query)
from .utils.pubsub import (parse_income_message,
                           subscribe_response_topic_wrapper)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["sensor"]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    _LOGGER.debug(f"setup data: {config.get(DOMAIN)}")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry."""
    _LOGGER.debug("Starting setup in init")
    conf = entry.data
    _LOGGER.debug("Executing hass.data.setdefault")
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = Client(hass)
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    geo = hass.states.get("zone.home")
    geo_str = f'{geo.attributes["latitude"]}, {geo.attributes["longitude"]}'
    _LOGGER.debug(f"Set geo to {geo_str}")

    if CONF_IPFS_GW in conf:
        hass.data[DOMAIN]["ipfs_gw"] = conf[CONF_IPFS_GW]
    else:
        hass.data[DOMAIN]["ipfs_gw"] = IPFS_GW
    _LOGGER.debug(f"Set ipfs_gw to {hass.data[DOMAIN]['ipfs_gw']}")

    if CONF_IS_W3GW in conf:

        def ipfs_w3gw_auth_wrapper():
            return web_3_auth(conf[CONF_ADMIN_SEED])

        hass.data[DOMAIN]["ipfs_gw_auth"] = ipfs_w3gw_auth_wrapper
        _LOGGER.debug(f"Set ipfs_gw_auth to web3-auth format")

    elif CONF_IPFS_GATEWAY_AUTH in conf:

        def ipfs_auth_wrapper():
            return conf[CONF_IPFS_GATEWAY_AUTH], conf[CONF_IPFS_GATEWAY_PWD]

        hass.data[DOMAIN]["ipfs_gw_auth"] = ipfs_auth_wrapper
        _LOGGER.debug(f"Set ipfs_gw_auth to login/password")
    else:

        def ipfs_empty_auth_wrapper():
            return ()

        hass.data[DOMAIN]["ipfs_gw_auth"] = ipfs_empty_auth_wrapper
        _LOGGER.debug(f"Set ipfs_gw_auth to empty")

    account = Account(seed=conf[CONF_ADMIN_SEED], crypto_type=KeypairType.ED25519)
    hass.data[DOMAIN]["account_addr"] = account.get_address()
    hass.data[DOMAIN]["liability"] = Liability(account=account)

    async def get_kwh_to_compensate(call):
        """

        :param call:
        """
        try:

            def callback(obj, update_nr, subscription_id):
                response = parse_income_message(obj["params"]["result"]["data"])
                if response["address"] == hass.data[DOMAIN]["account_addr"]:
                    _LOGGER.debug(f"response in {LAST_COMPENSATION_DATE_RESPONSE_TOPIC}: {response}")
                    hass.services.call(
                        domain="notify",
                        service="persistent_notification",
                        service_data=dict(
                            message=f"Last compensated: {response['last_compensation_date'] or 'Never'}, "
                                    f"to compensate: {response['kwh_to_compensate']} kWh.",
                            title="Got amount of kWh to compensate!",
                        ),
                    )
                    hass.data[DOMAIN][entry.entry_id].set_to_compensate(response["kwh_to_compensate"])
                    hass.data[DOMAIN][entry.entry_id].set_total_compensated(kwh - response["kwh_to_compensate"])
                    hass.data[DOMAIN][entry.entry_id].set_last_compensation_date(
                        response["last_compensation_date"] or "Never"
                    )
                    hass.data[DOMAIN][entry.entry_id].publish_updates()
                    _LOGGER.debug(
                        f"Updated {DOMAIN}.to_compensate with {response['kwh_to_compensate']}, "
                        f"{DOMAIN}.previous_compensation_date with {response['last_compensation_date'] or 'Never'}"
                    )
                    return True

            resp_sub = asyncio.ensure_future(
                subscribe_response_topic_wrapper(LAST_COMPENSATION_DATE_RESPONSE_TOPIC, callback, 10)
            )
            await asyncio.sleep(1)
            # TODO
            # Get kwh from energy
            kwh = 505.0
            await send_last_compensation_date_query(address=hass.data[DOMAIN]["account_addr"], kwh_current=kwh)
            await resp_sub
        except asyncio.TimeoutError:
            _LOGGER.error(f"Failed to get amount of kWh to compensate. Pubsub timeout. Notifying the user")
            await hass.services.async_call(
                domain="notify",
                service="persistent_notification",
                service_data=dict(
                    message=f"Failed to get amount of kWh to compensate. Robonomics PubSub timeout.",
                    title="PubSub timeout!",
                ),
            )

        except Exception as e:
            _LOGGER.error(f"Failed to get amount of kWh to compensate: {e}")
            await hass.services.async_call(
                domain="notify",
                service="persistent_notification",
                service_data=dict(
                    message=f"Internal error, check logs for more detail.",
                    title="Failed to get amount of kWh to compensate!",
                ),
            )

    async def compensate_kwh(call):
        """

        :param call:
        """
        try:

            def callback(obj, update_nr, subscription_id):
                response = parse_income_message(obj["params"]["result"]["data"])
                if response["address"] == hass.data[DOMAIN]["account_addr"]:
                    _LOGGER.debug(f"response in {LIABILITY_REPORT_TOPIC}: {response}")
                    if response["success"]:
                        hass.services.call(
                            domain="notify",
                            service="persistent_notification",
                            service_data=dict(
                                message=f"Successfully compensated carbon footprint. "
                                        f"See Robonomics Liability report {response['report']} for details.",
                                title="Successful compensation!",
                            ),
                        )
                        hass.data[DOMAIN][entry.entry_id].set_to_compensate("Yet unknown")
                        hass.data[DOMAIN][entry.entry_id].set_total_compensated(response["total"])
                        hass.data[DOMAIN][entry.entry_id].set_last_compensation_date(f"{date.today()}")
                        hass.data[DOMAIN][entry.entry_id].publish_updates()
                    else:
                        hass.services.call(
                            domain="notify",
                            service="persistent_notification",
                            service_data=dict(
                                message=f"Failed to burn carbon units. Internal agent error.",
                                title="Offsetting agent error!",
                            ),
                        )
                    return True

            resp_sub = asyncio.ensure_future(subscribe_response_topic_wrapper(LIABILITY_REPORT_TOPIC, callback, 120))
            await asyncio.sleep(1)

            kwh = hass.data[DOMAIN][entry.entry_id].to_compensate
            coordinates = geo_str
            _LOGGER.debug(f"Set kwh to {kwh}, coordinates to {coordinates}.")
            await send_offset_query(
                geo=coordinates,
                kwh=kwh,
                ipfs_gw=hass.data[DOMAIN]["ipfs_gw"],
                ipfs_auth=hass.data[DOMAIN]["ipfs_gw_auth"](),
                promisee=hass.data[DOMAIN]["account_addr"],
                liability_signer=hass.data[DOMAIN]["liability"],
                hass=hass,
            )

            await resp_sub
        except asyncio.TimeoutError:
            _LOGGER.error(f"Failed to compensate kWh. Pubsub timeout. Notifying the user.")
            await hass.services.async_call(
                domain="notify",
                service="persistent_notification",
                service_data=dict(
                    message=f"Failed to compensate kWh. Robonomics PubSub timeout. "
                            f"Check amount of kWh to compensate in case assets were burned.",
                    title="PubSub timeout!",
                ),
            )

        except Exception as e:
            _LOGGER.error(f"Failed to compensate kWh: {e}")
            await hass.services.async_call(
                domain="notify",
                service="persistent_notification",
                service_data=dict(
                    message=f"Internal error, check logs for more detail.",
                    title="Failed to compensate!",
                ),
            )

    hass.services.async_register(DOMAIN, "get_amount_of_kwh_to_compensate", get_kwh_to_compensate)
    hass.services.async_register(DOMAIN, "compensate_kwh", compensate_kwh)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
