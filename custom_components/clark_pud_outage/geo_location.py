from __future__ import annotations

from collections.abc import Callable
from typing import Any

from homeassistant.components.geo_location import GeolocationEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import Outage
from .const import DOMAIN, OUTAGE_ENTITY_EXPIRATION
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
        new_entities: list[ClarkPUDOutageGeoLocationEvent] = []

        for outage in coordinator.data.open_outages:
            if outage.key in entities:
                continue
            entity = ClarkPUDOutageGeoLocationEvent(coordinator, outage.key)
            entities[outage.key] = entity
            new_entities.append(entity)

        for key in list(entities):
            if key in latest_keys:
                continue
            entities[key].set_missing()

        if new_entities:
            async_add_entities(new_entities)

    _sync_entities()
    entry.async_on_unload(coordinator.async_add_listener(_sync_entities))


class ClarkPUDOutageGeoLocationEvent(
    GeolocationEvent,
):
    """Map event for a single Clark PUD outage."""

    _attr_icon = "mdi:flash-alert"
    _attr_has_entity_name = True
    _attr_source = DOMAIN

    def __init__(
        self, coordinator: ClarkPUDOutageDataUpdateCoordinator, outage_key: str
    ) -> None:
        super().__init__()
        self.coordinator = coordinator
        self._outage_key = outage_key
        self._attr_unique_id = f"outage_{outage_key}"
        self._attr_external_id = outage_key
        self._attr_name = f"Outage {outage_key}"
        self._unsub_coordinator: Callable[[], None] | None = None
        self._unsub_expiration: Callable[[], None] | None = None
        self._missing = False
        self._update_attributes()

    def _find_outage(self) -> Outage | None:
        for outage in self.coordinator.data.open_outages:
            if outage.key == self._outage_key:
                return outage
        return None

    def _update_attributes(self) -> None:
        outage = self._find_outage()
        if outage is None:
            self._missing = True
            self._attr_latitude = None
            self._attr_longitude = None
            self._attr_extra_state_attributes = {}
            return

        self._missing = False
        if self._unsub_expiration is not None:
            self._unsub_expiration()
            self._unsub_expiration = None
        self._attr_latitude = outage.lat
        self._attr_longitude = outage.lon
        self._attr_extra_state_attributes = {
            "affected_customer_count": outage.affected_customer_count,
            "reported": outage.reported,
            "estimated_restoration": outage.estimated_restoration,
            "cause": outage.cause,
            "status": outage.status,
        }

    @callback
    def set_missing(self) -> None:
        """Mark the outage as missing and schedule removal after the grace period."""
        self._update_attributes()
        self.async_write_ha_state()

        if self._unsub_expiration is not None:
            return

        async def _expire(_now) -> None:
            if self._find_outage() is not None:
                self._unsub_expiration = None
                return

            await self.async_remove()

        self._unsub_expiration = async_call_later(
            self.hass,
            OUTAGE_ENTITY_EXPIRATION,
            _expire,
        )

    async def async_added_to_hass(self) -> None:
        """Subscribe to coordinator updates when entity is added."""
        await super().async_added_to_hass()

        @callback
        def _handle_update() -> None:
            self._update_attributes()
            self.async_write_ha_state()

        self._unsub_coordinator = self.coordinator.async_add_listener(_handle_update)

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from coordinator updates when entity is removed."""
        if self._unsub_coordinator is not None:
            self._unsub_coordinator()
            self._unsub_coordinator = None
        if self._unsub_expiration is not None:
            self._unsub_expiration()
            self._unsub_expiration = None
        await super().async_will_remove_from_hass()
