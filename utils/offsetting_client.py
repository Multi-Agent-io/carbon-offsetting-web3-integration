"""
Handles interacting with offsetting agent
"""

import logging
from time import time

import ipfshttpclient2

from ..const import LAST_COMPENSATION_DATE_QUERY_TOPIC, LIABILITY_QUERY_TOPIC
from .pubsub import pubsub_send
from .thread_wrapper import to_thread

_LOGGER = logging.getLogger(__name__)


@to_thread
def ipfs_client_thread_wrapper(ipfs_gw, ipfs_auth, content):
    with ipfshttpclient2.connect(addr=ipfs_gw, auth=ipfs_auth) as client:
        return client.add_json(content)


async def send_offset_query(geo, kwh, ipfs_gw, ipfs_auth, promisee, liability_signer, hass):
    """

    :param geo:
    :param kwh:
    :param ipfs_gw:
    :param ipfs_auth:
    :param promisee:
    :param liability_signer:
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


async def send_last_compensation_date_query(address, kwh_current):
    """

    :param address:
    :param kwh_current:
    """
    last_compensation_date_query = dict(address=address, kwh_current=kwh_current, timestamp=time())
    _LOGGER.debug(f"last_compensation_date_query: {last_compensation_date_query}")
    await pubsub_send(LAST_COMPENSATION_DATE_QUERY_TOPIC, str(last_compensation_date_query))
