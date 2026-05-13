from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ClarkPUDOutageDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class ClarkPUDSensorEntityDescription(SensorEntityDescription):
    """Entity description for Clark PUD sensors."""

    suggested_object_id: str


SENSOR_DESCRIPTIONS: tuple[ClarkPUDSensorEntityDescription, ...] = (
    ClarkPUDSensorEntityDescription(
        key="total_affected_customer_count",
        name="Total affected customers",
        translation_key="total_affected_customer_count",
        suggested_object_id="clark_pud_outage_total_affected_customers",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ClarkPUDSensorEntityDescription(
        key="recently_restored_customer_count",
        name="Recently restored customers",
        translation_key="recently_restored_customer_count",
        suggested_object_id="clark_pud_outage_recently_restored_customers",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ClarkPUDSensorEntityDescription(
        key="open_outage_count",
        name="Open outages",
        translation_key="open_outage_count",
        suggested_object_id="clark_pud_outage_open_outages",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ClarkPUDSensorEntityDescription(
        key="generated",
        name="Data generated",
        translation_key="generated",
        suggested_object_id="clark_pud_outage_data_generated",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Clark PUD outage sensors from a config entry."""
    coordinator: ClarkPUDOutageDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        ClarkPUDSensorEntity(coordinator, description)
        for description in SENSOR_DESCRIPTIONS
    )


class ClarkPUDSensorEntity(
    CoordinatorEntity[ClarkPUDOutageDataUpdateCoordinator],
    SensorEntity,
):
    """Base sensor for Clark PUD outage data."""

    entity_description: ClarkPUDSensorEntityDescription

    def __init__(
        self,
        coordinator: ClarkPUDOutageDataUpdateCoordinator,
        entity_description: ClarkPUDSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_unique_id = f"summary_{entity_description.key}"
        self._attr_has_entity_name = True
        self._attr_suggested_object_id = entity_description.suggested_object_id

    @property
    def native_value(self):
        """Return sensor state."""
        snapshot = self.coordinator.data
        if self.entity_description.key == "total_affected_customer_count":
            return snapshot.total_affected_customer_count
        if self.entity_description.key == "recently_restored_customer_count":
            return snapshot.recently_restored_customer_count
        if self.entity_description.key == "open_outage_count":
            return len(snapshot.open_outages)
        if self.entity_description.key == "generated":
            return snapshot.generated
        return None

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Expose outage details on the outage-count sensor."""
        if self.entity_description.key != "open_outage_count":
            return None

        snapshot = self.coordinator.data
        return {
            "total_affected_customer_count": snapshot.total_affected_customer_count,
            "recently_restored_customer_count": snapshot.recently_restored_customer_count,
            "generated": snapshot.generated,
            "open_outages": [
                {
                    "key": outage.key,
                    "lat": outage.lat,
                    "lon": outage.lon,
                    "affected_customer_count": outage.affected_customer_count,
                    "reported": outage.reported,
                    "estimated_restoration": outage.estimated_restoration,
                    "cause": outage.cause,
                    "status": outage.status,
                }
                for outage in snapshot.open_outages
            ],
        }
