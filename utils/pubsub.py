import asyncio
import logging
import typing as tp
from ast import literal_eval

from robonomicsinterface import Account, PubSub

from ..const import AGENT_NODE_MULTIADDR
from .thread_wrapper import to_thread

_LOGGER = logging.getLogger(__name__)


def parse_income_message(raw_data: tp.List[tp.Any]) -> dict:
    """
    Parse income PubSub Message.

    :param raw_data: Income PubSub Message.

    :return: technics, amount, promisee, promisee_signature.

    """

    for i in range(len(raw_data)):
        raw_data[i] = chr(raw_data[i])
    data: str = "".join(raw_data)
    data_dict: tp.Dict[tp.Union[dict, int, str]] = literal_eval(data)

    return data_dict


async def pubsub_send(topic: str, data: tp.Any):
    """
    Send data to a topic via PubSub

    :param topic: Topic to send to.
    :param data: Data to send.

    """

    _LOGGER.debug(f"Sending data {data} to topic {topic}.")
    account = Account()
    pubsub = PubSub(account)
    _LOGGER.debug(f"PubSub connect result: {pubsub.connect(AGENT_NODE_MULTIADDR)}")
    await asyncio.sleep(1)
    _LOGGER.debug(f"PubSub send result: {pubsub.publish(topic, str(data))}")


@to_thread
def subscribe_response_topic(request_topic, callback):
    account_ = Account()
    pubsub_ = PubSub(account_)
    _LOGGER.debug(f"Subscribing to topic '{request_topic}'")
    pubsub_.subscribe(request_topic, result_handler=callback)


async def subscribe_response_topic_wrapper(request_topic, callback, timeout):
    await asyncio.wait_for(subscribe_response_topic(request_topic, callback), timeout=timeout)
