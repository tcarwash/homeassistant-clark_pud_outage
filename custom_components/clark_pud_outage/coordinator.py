from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ClarkPUDOutageApiClient, OutageSnapshot

_LOGGER = logging.getLogger(__name__)


class ClarkPUDOutageDataUpdateCoordinator(DataUpdateCoordinator[OutageSnapshot]):
    """Coordinator to fetch Clark PUD outage data."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: ClarkPUDOutageApiClient,
        update_interval: timedelta,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Clark PUD Outage Data",
            update_interval=update_interval,
        )
        self.api = api

    async def _async_update_data(self) -> OutageSnapshot:
        try:
            return await self.api.async_fetch_snapshot()
        except Exception as err:
            raise UpdateFailed(f"Failed to refresh outage data: {err}") from err
