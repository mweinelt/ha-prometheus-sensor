"""Prometheus Sensor component."""
from datetime import timedelta
import logging
from typing import Dict, Final
from urllib.parse import urljoin

import aiohttp
import voluptuous as vol

from homeassistant.components.sensor import (
    PLATFORM_SCHEMA as SENSOR_PLATFORM_SCHEMA,
    SensorEntity,
)
from homeassistant.components.sensor.const import (
    DEVICE_CLASSES_SCHEMA,
    STATE_CLASSES_SCHEMA,
)
from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_NAME,
    CONF_UNIQUE_ID,
    CONF_UNIT_OF_MEASUREMENT,
    CONF_URL,
    STATE_PROBLEM,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType, StateType
from homeassistant.util import Throttle

_LOGGER: Final = logging.getLogger(__name__)

DEFAULT_URL: Final = "http://localhost:9090"
CONF_QUERIES: Final = "queries"
CONF_EXPR: Final = "expr"
CONF_STATE_CLASS: Final = "state_class"
MIN_TIME_BETWEEN_UPDATES: Final = timedelta(seconds=60)

_QUERY_SCHEMA: Final = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_UNIQUE_ID): cv.string,
        vol.Optional(CONF_UNIT_OF_MEASUREMENT): cv.string,
        vol.Required(CONF_EXPR): cv.string,
        vol.Optional(CONF_DEVICE_CLASS): DEVICE_CLASSES_SCHEMA,
        vol.Optional(CONF_STATE_CLASS): STATE_CLASSES_SCHEMA,
    }
)

PLATFORM_SCHEMA: Final = SENSOR_PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_URL, default=DEFAULT_URL): cv.string,
        vol.Required(CONF_QUERIES): [_QUERY_SCHEMA],
    }
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
):
    """Set up the sensor platform."""
    session = async_get_clientsession(hass)
    url = config[CONF_URL]
    prometheus = Prometheus(url, session)

    queries = config[CONF_QUERIES]
    async_add_entities(
        [PrometheusSensor(prometheus, query) for query in queries],
        update_before_add=True,
    )


class Prometheus:
    """Wrapper for Prometheus API Requests."""

    def __init__(self, url: str, session: aiohttp.ClientSession) -> None:
        """Initialize the Prometheus API wrapper."""
        self._session = session
        self._url = urljoin(f"{url}/", "api/v1/query")

    async def query(self, expr: str) -> float | StateType:
        """Query expression response."""
        response = await self._session.get(self._url, params={"query": expr})
        if response.status != 200:
            _LOGGER.error(
                "Unexpected HTTP status code %s for expression '%s'",
                response.status,
                expr,
            )
            return STATE_UNKNOWN

        try:
            result = (await response.json())["data"]["result"]
        except (ValueError, KeyError) as error:
            _LOGGER.error("Invalid query response: %s", error)
            return STATE_UNKNOWN

        if not result:
            _LOGGER.error("Expression '%s' yielded no result", expr)
            return STATE_PROBLEM
        elif len(result) > 1:
            _LOGGER.error("Expression '%s' yielded multiple metrics", expr)
            return STATE_PROBLEM

        value = float(result[0]["value"][1])

        _LOGGER.debug("Expression '%s' yields result %f", expr, value)

        return value


class PrometheusSensor(SensorEntity):
    """Sensor entity representing the result of a PromQL expression."""

    def __init__(self, prometheus: Prometheus, query: Dict[str, str]) -> None:
        """Initialize the sensor."""
        self._expr = query[CONF_EXPR]
        self._prometheus: Prometheus = prometheus

        self._attr_name = query[CONF_NAME]
        self._attr_unique_id = query.get(CONF_UNIQUE_ID)
        self._attr_native_unit_of_measurement = query.get(CONF_UNIT_OF_MEASUREMENT)
        self._attr_state_class = query.get(CONF_STATE_CLASS)
        self._attr_device_class = query.get(CONF_DEVICE_CLASS)

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self) -> None:
        """Update state by executing query."""
        self._attr_native_value = await self._prometheus.query(self._expr)
