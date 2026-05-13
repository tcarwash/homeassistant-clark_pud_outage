from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from homeassistant.components.geo_location import GeolocationEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import Outage
from .const import DOMAIN
from .coordinator import ClarkPUDOutageDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Clark PUD outage geolocation entities."""
    coordinator: ClarkPUDOutageDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: dict[str, ClarkPUDOutageGeoLocationEvent] = {}

    @callback
    def _sync_entities() -> None:
        latest_keys = {outage.key for outage in coordinator.data.open_outages}

        for outage in coordinator.data.open_outages:
            if outage.key in entities:
                continue
            entities[outage.key] = ClarkPUDOutageGeoLocationEvent(
                coordinator, outage.key
            )

        for key in list(entities):
            if key in latest_keys:
                continue
            hass.async_create_task(entities[key].async_remove())
            del entities[key]

        new_entities = [
            entity for key, entity in entities.items() if not entity.added_to_hass
        ]
        if new_entities:
            async_add_entities(new_entities)

    _sync_entities()
    entry.async_on_unload(coordinator.async_add_listener(_sync_entities))


class ClarkPUDOutageGeoLocationEvent(
    CoordinatorEntity[ClarkPUDOutageDataUpdateCoordinator],
    GeolocationEvent,
):
    """Map event for a single Clark PUD outage."""

    _attr_icon = "mdi:flash-alert"
    _attr_has_entity_name = True

    def __init__(
        self, coordinator: ClarkPUDOutageDataUpdateCoordinator, outage_key: str
    ) -> None:
        super().__init__(coordinator)
        self._outage_key = outage_key
        self._attr_unique_id = f"outage_{outage_key}"

    @property
    def _outage(self) -> Outage | None:
        for outage in self.coordinator.data.open_outages:
            if outage.key == self._outage_key:
                return outage
        return None

    @property
    def source(self) -> str:
        """Return the source of the event."""
        return DOMAIN

    @property
    def name(self) -> str:
        """Return the event name."""
        return f"Outage {self._outage_key}"

    @property
    def external_id(self) -> str:
        """Return a unique id from the source."""
        return self._outage_key

    @property
    def latitude(self) -> float | None:
        """Return latitude for the event."""
        outage = self._outage
        return outage.lat if outage else None

    @property
    def longitude(self) -> float | None:
        """Return longitude for the event."""
        outage = self._outage
        return outage.lon if outage else None

    @property
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return event details in attributes."""
        outage = self._outage
        if outage is None:
            return {}

        return {
            "affected_customer_count": outage.affected_customer_count,
            "reported": outage.reported,
            "estimated_restoration": outage.estimated_restoration,
            "cause": outage.cause,
            "status": outage.status,
        }
