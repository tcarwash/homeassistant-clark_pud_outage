from datetime import timedelta

DOMAIN = "clark_pud_outage"
NAME = "Clark PUD Outage Data"
OUTAGE_DATA_URL = "https://www.clarkpublicutilities.com/outage-map/data.js"

CONF_SCAN_INTERVAL_MINUTES = "scan_interval_minutes"
DEFAULT_SCAN_INTERVAL_MINUTES = 5
DEFAULT_TIMEOUT_SECONDS = 15
DEFAULT_UPDATE_INTERVAL = timedelta(minutes=DEFAULT_SCAN_INTERVAL_MINUTES)
