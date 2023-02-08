"""Custom exceptions for the Robonomics integration."""
from homeassistant.exceptions import HomeAssistantError


class InvalidSeed(HomeAssistantError):
    """Given sub admin seed is not correct"""


class InvalidIPFSCreds(HomeAssistantError):
    """
    Given IPFS credential don't match (i.e. no password given for auth or auth/pwd given
        alongside with web3-auth tick).
    """
