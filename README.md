# Clark PUD Outage Data for Home Assistant

## Installation

1. Copy this repository into your Home Assistant config folder under `custom_components/clark_pud_outage`.
2. Restart Home Assistant.
3. Add the integration from Settings > Devices & Services > Add Integration.

## What It Exposes

- Sensor: Total affected customers
- Sensor: Recently restored customers
- Sensor: Open outages
- Sensor: Data generated timestamp
- Geo-location events: One map marker per open outage

The `open_outages` sensor includes full outage details as attributes (`key`, coordinates,
affected customer count, reported time, estimated restoration, cause, and status), which can
be used in dashboards, templates, and automations.
