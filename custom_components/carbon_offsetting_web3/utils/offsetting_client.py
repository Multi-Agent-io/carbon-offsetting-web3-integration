"""
Handles interacting with offsetting agent
"""

import logging
from time import time

import ipfshttpclient2
import robonomicsinterface

from ..const import LAST_COMPENSATION_DATE_QUERY_TOPIC, LIABILITY_QUERY_TOPIC
from .pubsub import pubsub_send
from .thread_wrapper import to_thread

_LOGGER = logging.getLogger(__name__)


@to_thread
def ipfs_client_thread_wrapper(ipfs_gw: str, ipfs_auth: tuple[str, str], content: dict):
    """
    Wrapped IPFS 'Add JSON' functionality to be used in async methods. Uploads any dict (JSON) to IPFS.

    :param ipfs_gw: IPFS gateway to upload through.
    :param ipfs_auth: Gateway auth header (login, password).
    :param content: Content to upload.

    :return: IPFS CID.

    """
    with ipfshttpclient2.connect(addr=ipfs_gw, auth=ipfs_auth) as client:
        return client.add_json(content)


async def send_offset_query(
    geo: str,
    kwh: float,
    ipfs_gw: str,
    ipfs_auth: dict[str, str],
    promisee: str,
    liability_signer: robonomicsinterface.Liability,
):
    """
    Gather query message to send to an Agent to create new compensation liability.

    :param geo: Home coordinates.
    :param kwh: Total energy consumption, subtracted with energy production.
    :param ipfs_gw: IPFS gateway to upload liability technics through.
    :param ipfs_auth: Gateway auth header (login, password).
    :param promisee: Promisee (client) address in Robonomics Parachain.
    :param liability_signer: robonomicsinterface.Liability instance with a promisee seed.

    """

    content = dict(geo=geo, kwh=kwh)
    technics = await ipfs_client_thread_wrapper(ipfs_gw, ipfs_auth, content)
    economics = 0
    promisee_signature = liability_signer.sign_liability(technics, economics)

    liability_query = dict(
        technics=technics,
        economics=economics,
        promisee=promisee,
        promisee_signature=dict(ED25519=promisee_signature),
        timestamp=time(),
    )
    _LOGGER.debug(f"liability_query: {liability_query}")
    await pubsub_send(LIABILITY_QUERY_TOPIC, str(liability_query))


async def send_last_compensation_date_query(address: str, kwh_current: float):
    """
    Gather query message to send to an Agent to get last compensation date and total amount of kWh compensated.

    :param address: Householder address in Robonomics Parachain.
    :param kwh_current: Current total amount of kWh consumed subtracted with current total amount of kWh produced.

    """

    last_compensation_date_query = dict(address=address, kwh_current=kwh_current, timestamp=time())
    _LOGGER.debug(f"last_compensation_date_query: {last_compensation_date_query}")
    await pubsub_send(LAST_COMPENSATION_DATE_QUERY_TOPIC, str(last_compensation_date_query))
