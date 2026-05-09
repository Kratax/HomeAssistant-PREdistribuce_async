"""The PRE Distribuce integration."""
import logging

_LOGGER = logging.getLogger(__name__)
DOMAIN = "predistribuce_async"

async def async_setup(hass, config):
    """Set up the PRE Distribuce component."""
    # Toto zajistí, že se doména v HA správně zaregistruje
    return True
