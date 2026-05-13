from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ClarkPUDOutageApiClient
from .const import (
    CONF_SCAN_INTERVAL_MINUTES,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DEFAULT_TIMEOUT_SECONDS,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
)
from .coordinator import ClarkPUDOutageDataUpdateCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.GEO_LOCATION]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Clark PUD Outage Data integration."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Clark PUD Outage Data from a config entry."""
    session = async_get_clientsession(hass)
    api = ClarkPUDOutageApiClient(
        session=session,
        timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
    )

    interval_minutes = entry.options.get(
        CONF_SCAN_INTERVAL_MINUTES,
        DEFAULT_SCAN_INTERVAL_MINUTES,
    )
    update_interval = (
        DEFAULT_UPDATE_INTERVAL
        if interval_minutes == DEFAULT_SCAN_INTERVAL_MINUTES
        else timedelta(minutes=interval_minutes)
    )

    coordinator = ClarkPUDOutageDataUpdateCoordinator(
        hass=hass,
        api=api,
        update_interval=update_interval,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
