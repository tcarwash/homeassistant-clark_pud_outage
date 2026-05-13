from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import re
from typing import Any

from aiohttp import ClientSession
from homeassistant.exceptions import HomeAssistantError

from .const import OUTAGE_DATA_URL


class ClarkPUDOutageApiError(HomeAssistantError):
    """Raised when Clark PUD outage data cannot be fetched or parsed."""


@dataclass(frozen=True)
class Outage:
    """One open outage from the Clark PUD feed."""

    key: str
    lat: float
    lon: float
    affected_customer_count: int
    reported: datetime | None
    estimated_restoration: datetime | None
    cause: str | None
    status: str | None


@dataclass(frozen=True)
class OutageSnapshot:
    """Full snapshot from the Clark PUD feed."""

    generated: datetime | None
    total_affected_customer_count: int
    recently_restored_customer_count: int
    open_outages: tuple[Outage, ...]


def _parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        return None

    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def parse_data_js(payload: str) -> OutageSnapshot:
    """Parse JSONP response from data.js into an outage snapshot."""
    match = re.search(r"gksUpdateOutageData\((.*)\)\s*;?\s*$", payload.strip(), re.DOTALL)
    if not match:
        raise ClarkPUDOutageApiError("Invalid response shape from outage data endpoint")

    try:
        root = json.loads(match.group(1))
    except json.JSONDecodeError as err:
        raise ClarkPUDOutageApiError("Unable to decode outage data payload") from err

    if root.get("ok") is not True:
        raise ClarkPUDOutageApiError("Outage data endpoint returned unsuccessful result")

    result = root.get("result")
    if not isinstance(result, dict):
        raise ClarkPUDOutageApiError("Missing result object in outage data")

    outages: list[Outage] = []
    for item in result.get("openOutages", []):
        if not isinstance(item, dict):
            continue
        key = str(item.get("key", ""))
        if not key:
            continue
        outages.append(
            Outage(
                key=key,
                lat=float(item.get("lat", 0.0)),
                lon=float(item.get("lon", 0.0)),
                affected_customer_count=int(item.get("affectedCustomerCount", 0)),
                reported=_parse_datetime(item.get("reported")),
                estimated_restoration=_parse_datetime(item.get("estimatedRestoration")),
                cause=item.get("cause"),
                status=item.get("status"),
            )
        )

    return OutageSnapshot(
        generated=_parse_datetime(result.get("generated")),
        total_affected_customer_count=int(result.get("totalAffectedCustomerCount", 0)),
        recently_restored_customer_count=int(result.get("recentlyRestoredCustomerCount", 0)),
        open_outages=tuple(outages),
    )


class ClarkPUDOutageApiClient:
    """API client for Clark PUD outage data."""

    def __init__(self, session: ClientSession, timeout_seconds: int) -> None:
        self._session = session
        self._timeout_seconds = timeout_seconds

    async def async_fetch_snapshot(self) -> OutageSnapshot:
        """Fetch and parse current outage snapshot."""
        try:
            async with self._session.get(
                OUTAGE_DATA_URL,
                timeout=self._timeout_seconds,
            ) as response:
                response.raise_for_status()
                payload = await response.text()
        except Exception as err:
            raise ClarkPUDOutageApiError("Unable to fetch outage data") from err

        return parse_data_js(payload)
