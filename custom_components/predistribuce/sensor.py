import math
import logging
import voluptuous as vol
from datetime import datetime, date
from homeassistant.components.sensor import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import get_shared_coordinator

_LOGGER = logging.getLogger(__name__)

DOMAIN = "predistribuce"
CONF_CMD = "receiver_command_id"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_CMD): cv.string,
})

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    conf_cmd = config.get(CONF_CMD)
    coordinator = await get_shared_coordinator(hass, conf_cmd)
    
    async_add_entities([PreDistribuceTimeSensor(coordinator, conf_cmd, "HDO čas do změny tarifu")])

class PreDistribuceTimeSensor(CoordinatorEntity):
    def __init__(self, coordinator, cmd, name):
        super().__init__(coordinator)
        self.cmd = cmd
        self._attr_name = name
        self._attr_icon = "mdi:av-timer"
        self._attr_unit_of_measurement = "min"
        self._attr_unique_id = f"{DOMAIN}_time_{cmd}"

    @property
    def state(self):
        schedule = self.coordinator.data
        if not schedule: return None

        time_now = datetime.now().time()
        
        # Zjistíme, v jakém jsme intervalu
        for period in schedule:
            start_time = datetime.strptime(period["start"], '%H:%M').time()
            end_time = datetime.strptime(period["end"], '%H:%M').time()
            
            if start_time <= time_now < end_time or (period["end"] == "23:59" and start_time <= time_now):
                # Vypočteme, kolik zbývá do konce aktuálního bloku
                end_datetime = datetime.combine(date.today(), end_time)
                now_datetime = datetime.combine(date.today(), time_now)
                zbyva_minut = (end_datetime - now_datetime).total_seconds() / 60
                
                return math.floor(zbyva_minut)
        return 0

    @property
    def extra_state_attributes(self):
        # Nyní máš v atributech JSON strukturu použitelnou pro ApexCharts grafy!
        schedule = self.coordinator.data
        if not schedule: return {}
        
        # Zjistíme aktuální tarif pro přehlednost v atributech
        current_tariff = "V"
        time_now = datetime.now().time()
        for p in schedule:
            st = datetime.strptime(p["start"], '%H:%M').time()
            en = datetime.strptime(p["end"], '%H:%M').time()
            if st <= time_now < en or (p["end"] == "23:59" and st <= time_now):
                current_tariff = p["tariff"]
        
        return {
            "schedule": schedule,
            "current_tariff": current_tariff
        }
