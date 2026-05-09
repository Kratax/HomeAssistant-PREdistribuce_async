import logging
from datetime import timedelta, date
from lxml import html
import async_timeout

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)
DOMAIN = "predistribuce"

def parse_html_to_schedule(html_string):
    """Vyparsuje surové HTML a vrátí čisté pole časů (JSON-friendly)."""
    tree = html.fromstring(html_string)
    tariffs_raw = tree.xpath('//div[@id="component-hdo-dnes"]/div[@class="hdo-bar"]/span[starts-with(@class, "hdo")]/@class')
    times_raw = tree.xpath('//div[@id="component-hdo-dnes"]/div/span[@class="span-overflow"]/@title')
    
    if not tariffs_raw or not times_raw:
        raise ValueError("Nelze najít HDO data. Změnil se design PRE?")

    tariffs = [x[3].upper() for x in tariffs_raw] # Vytáhne 'N' nebo 'V'
    starts = [x[0:5].upper() for x in times_raw]

    schedule = []
    for i in range(len(starts)):
        start = starts[i]
        end = starts[i+1] if i + 1 < len(starts) else "23:59"
        schedule.append({"start": start, "end": end, "tariff": tariffs[i]})
        
    return schedule

async def get_shared_coordinator(hass, cmd):
    """Vytvoří a sdílí jeden DataUpdateCoordinator pro celou integraci."""
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
        
    if cmd not in hass.data[DOMAIN]:
        async def async_fetch_data():
            session = async_get_clientsession(hass)
            today = date.today()
            url = f"https://www.predistribuce.cz/cs/potrebuji-zaridit/zakaznici/stav-hdo/?povel={cmd}&den_od={today.day}&mesic_od={today.month}&rok_od={today.year}&den_do={today.day}&mesic_do={today.month}&rok_do={today.year}"
            
            try:
                async with async_timeout.timeout(15):
                    response = await session.get(url)
                    response.raise_for_status()
                    html_text = await response.text()
                    
                # Parsování lxml je blokující operace, spustíme ji bezpečně mimo hlavní smyčku
                schedule = await hass.async_add_executor_job(parse_html_to_schedule, html_text)
                return schedule
                
            except Exception as e:
                raise UpdateFailed(f"Chyba komunikace s PRE: {e}")

        coordinator = DataUpdateCoordinator(
            hass,
            _LOGGER,
            name=f"PRE HDO {cmd}",
            update_method=async_fetch_data,
            update_interval=timedelta(minutes=15),
        )
        hass.data[DOMAIN][cmd] = coordinator
        await coordinator.async_config_entry_first_refresh()

    return hass.data[DOMAIN][cmd]
