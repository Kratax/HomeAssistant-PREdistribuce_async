import logging
import voluptuous as vol
from datetime import datetime, date
from homeassistant.components.binary_sensor import PLATFORM_SCHEMA, BinarySensorEntity
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import get_shared_coordinator

_LOGGER = logging.getLogger(__name__)

DOMAIN = "predistribuce"
CONF_CMD = "receiver_command_id"
CONF_SENSOR_NAME = "sensor_name"
CONF_PERIODS = "periods"
CONF_NAME = "name"
CONF_MINUTES = "minutes"

PERIOD_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_MINUTES): vol.All(vol.Coerce(int), vol.Range(min=1, max=300))
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_CMD): cv.string,
    vol.Optional(CONF_SENSOR_NAME): cv.string,
    vol.Optional(CONF_PERIODS): vol.All(cv.ensure_list, [PERIOD_SCHEMA])
})

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    conf_cmd = config.get(CONF_CMD)
    conf_name = config.get(CONF_SENSOR_NAME, "aktuálně")
    conf_periods = config.get(CONF_PERIODS, [])
    
    coordinator = await get_shared_coordinator(hass, conf_cmd)
    
    ents = [PreDistribuceBinary(coordinator, conf_cmd, 0, conf_name)]
    for pre in conf_periods:
        ents.append(PreDistribuceBinary(coordinator, conf_cmd, pre.get(CONF_MINUTES), pre.get(CONF_NAME)))
        
    async_add_entities(ents)

class PreDistribuceBinary(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator, cmd, minutes, name):
        super().__init__(coordinator)
        self.cmd = cmd
        self.minutes = minutes
        self._attr_name = f"HDO {name}" if name != "aktuálně" else "HDO"
        self._attr_unique_id = f"{DOMAIN}_hdo_{cmd}_{minutes}m"
        self._attr_device_class = "power"
        self._attr_icon = "mdi:flash"

    @property
    def is_on(self):
        schedule = self.coordinator.data
        if not schedule: return False

        time_now = datetime.now().time()
        
        for period in schedule:
            start_time = datetime.strptime(period["start"], '%H:%M').time()
            end_time = datetime.strptime(period["end"], '%H:%M').time()
            
            # Najdeme aktuální interval
            if start_time <= time_now < end_time or (period["end"] == "23:59" and start_time <= time_now):
                
                if period["tariff"] == "N":
                    if self.minutes == 0:
                        return True
                    else:
                        # Zjistíme, jestli NT běží ještě aspoň 'minutes' minut
                        end_dt = datetime.combine(date.today(), end_time)
                        now_dt = datetime.combine(date.today(), time_now)
                        zbyva_minut = (end_dt - now_dt).total_seconds() / 60
                        return zbyva_minut >= self.minutes
                else:
                    return False
        return False
