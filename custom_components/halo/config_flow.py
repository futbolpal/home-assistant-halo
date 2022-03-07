import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util.json import load_json

from .const import DATA_HALO_CONFIG, DOMAIN

ENTRY_DEFAULT_TITLE = "Halo"

_LOGGER = logging.getLogger(__name__)

class HaloFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):

    VERSION = 1

    def __init__(self):
        """Initialize a Halo flow."""
        self.data = {}

    async def async_step_import(self, import_info):
        # Store the imported config for other steps in this flow to access.
        self.data = import_info
        return self.async_create_entry(title=ENTRY_DEFAULT_TITLE, data=self.data)
