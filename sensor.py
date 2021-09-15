"""Prometheus Sensor component."""
from datetime import timedelta
import logging
from typing import Union
from urllib.parse import urljoin

import voluptuous as vol

from homeassistant.components.sensor import (
    DEVICE_CLASSES_SCHEMA,
    PLATFORM_SCHEMA as SENSOR_PLATFORM_SCHEMA,
    STATE_CLASSES_SCHEMA,
    SensorEntity,
)
from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_NAME,
    CONF_UNIT_OF_MEASUREMENT,
    CONF_URL,
    STATE_PROBLEM,
    STATE_UNKNOWN,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.util import Throttle

DEFAULT_URL = "http://localhost:9090"
CONF_QUERIES = "queries"
CONF_EXPR = "expr"
CONF_STATE_CLASS = "state_class"
MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=60)

_LOGGER = logging.getLogger(__name__)

_QUERY_SCHEMA = vol.Schema(
    {
        vol.Required(
            CONF_NAME,
        ): cv.string,
        vol.Optional(CONF_UNIT_OF_MEASUREMENT): cv.string,
        vol.Required(CONF_EXPR): cv.string,
        vol.Optional(CONF_DEVICE_CLASS): DEVICE_CLASSES_SCHEMA,
        vol.Optional(CONF_STATE_CLASS): STATE_CLASSES_SCHEMA,
    }
)

PLATFORM_SCHEMA = SENSOR_PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_URL, default=DEFAULT_URL): cv.string,
        vol.Required(CONF_QUERIES): [_QUERY_SCHEMA],
    }
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the sensor platform."""
    session = async_get_clientsession(hass)

    prometheus = Prometheus(config.get(CONF_URL), session)

    sensors = []
    for query in config.get("queries", {}):
        sensors.append(PrometheusSensor(prometheus, query))

    async_add_entities(sensors, update_before_add=True)


class Prometheus:
    """Wrapper for Prometheus API Requests."""

    def __init__(self, url: str, session) -> None:
        """Initialize the Prometheus API wrapper."""
        self._session = session
        self._url = urljoin(f"{url}/", "api/v1/query")

    async def query(self, expr) -> Union[str, float]:
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

        return result[0]["value"][1]


class PrometheusSensor(SensorEntity):
    """Sensor entity representing the result of a PromQL expression."""

    def __init__(self, prometheus: Prometheus, query: dict) -> None:
        """Initialize the sensor."""
        self._expr = query.get(CONF_EXPR)
        self._prometheus: Prometheus = prometheus

        self._attr_name = query.get(CONF_NAME)
        self._attr_unit_of_measurement = query.get(CONF_UNIT_OF_MEASUREMENT)
        self._attr_state_class = query.get(CONF_STATE_CLASS)
        self._attr_device_class = query.get(CONF_DEVICE_CLASS)

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self) -> None:
        """Update state by executing query."""
        self._attr_state = await self._prometheus.query(self._expr)
