"""Tests for Clark PUD outage API parsing."""

from custom_components.clark_pud_outage.api import parse_data_js


def test_parse_data_js_no_outages() -> None:
    """Parse payload with no outages."""
    payload = """gksUpdateOutageData({
      \"ok\": true,
      \"result\": {
        \"generated\": \"2026-05-07T21:25:03.349-07:00\",
        \"totalAffectedCustomerCount\": 0,
        \"recentlyRestoredCustomerCount\": 0,
        \"openOutages\": []
      }
    });"""

    snapshot = parse_data_js(payload)

    assert snapshot.total_affected_customer_count == 0
    assert snapshot.recently_restored_customer_count == 0
    assert snapshot.open_outages == ()
    assert snapshot.generated is not None


def test_parse_data_js_with_outage() -> None:
    """Parse payload with one outage."""
    payload = """gksUpdateOutageData({
      \"ok\": true,
      \"result\": {
        \"generated\": \"2026-05-12T19:55:03.488-07:00\",
        \"totalAffectedCustomerCount\": 7,
        \"recentlyRestoredCustomerCount\": 198,
        \"openOutages\": [
          {
            \"key\": \"41081\",
            \"lat\": 45.82771,
            \"lon\": -122.530304,
            \"affectedCustomerCount\": 7,
            \"reported\": \"2026-05-12T09:50:00.000-07:00\",
            \"estimatedRestoration\": \"2026-05-12T20:30:00.000-07:00\",
            \"cause\": \"Power line failure\",
            \"status\": null
          }
        ]
      }
    });"""

    snapshot = parse_data_js(payload)

    assert snapshot.total_affected_customer_count == 7
    assert snapshot.recently_restored_customer_count == 198
    assert len(snapshot.open_outages) == 1

    outage = snapshot.open_outages[0]
    assert outage.key == "41081"
    assert outage.lat == 45.82771
    assert outage.lon == -122.530304
    assert outage.affected_customer_count == 7
    assert outage.cause == "Power line failure"
