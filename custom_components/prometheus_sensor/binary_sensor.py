"""Prometheus Binary Sensor component."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

import probatio

from homeassistant.components.binary_sensor import (
    PLATFORM_SCHEMA as BINARY_SENSOR_PLATFORM_SCHEMA,
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_NAME,
    CONF_UNIQUE_ID,
    CONF_URL,
    CONF_VALUE_TEMPLATE,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv

from . import Prometheus, const

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeassistant.helpers.template import Template
    from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

    from . import QueryResult

from .const import CONF_EXPR, CONF_HEADERS, CONF_QUERIES, DEFAULT_URL

SCAN_INTERVAL = const.SCAN_INTERVAL

_QUERY_SCHEMA: Final = probatio.Schema(
    {
        probatio.Required(CONF_NAME): cv.string,
        probatio.Optional(CONF_UNIQUE_ID): cv.string,
        probatio.Required(CONF_EXPR): cv.string,
        probatio.Optional(CONF_VALUE_TEMPLATE): cv.template,
        probatio.Optional(CONF_DEVICE_CLASS): probatio.Coerce(BinarySensorDeviceClass),
    },
)

PLATFORM_SCHEMA: Final = BINARY_SENSOR_PLATFORM_SCHEMA.extend(
    {
        probatio.Optional(CONF_URL, default=DEFAULT_URL): cv.string,
        probatio.Optional(CONF_HEADERS): probatio.Schema({cv.string: cv.string}),
        probatio.Required(CONF_QUERIES): [_QUERY_SCHEMA],
    },
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    _: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensor platform."""
    session = async_get_clientsession(hass)
    url = config[CONF_URL]
    headers = config.get(CONF_HEADERS)
    prometheus = Prometheus(url, session, headers)

    async_add_entities(
        new_entities=[
            PrometheusBinarySensor(
                prometheus=prometheus,
                unique_id=query.get(CONF_UNIQUE_ID),
                device_name=query[CONF_NAME],
                expression=query[CONF_EXPR],
                value_template=query.get(CONF_VALUE_TEMPLATE),
                device_class=query.get(CONF_DEVICE_CLASS),
            )
            for query in config[CONF_QUERIES]
        ],
        update_before_add=True,
    )


class PrometheusBinarySensor(BinarySensorEntity):
    """Sensor entity representing the result of a PromQL expression."""

    def __init__(
        self,
        *,
        prometheus: Prometheus,
        unique_id: str | None,
        device_name: str,
        expression: str,
        value_template: Template,
        device_class: BinarySensorDeviceClass | None,
    ) -> None:
        """Initialize the sensor."""
        self._prometheus: Prometheus = prometheus
        self._expression = expression
        self._value_template = value_template

        self._attr_device_class = device_class
        self._attr_name = device_name
        self._attr_unique_id = unique_id

    async def async_update(self) -> None:
        """Update state by executing query."""
        result: QueryResult = await self._prometheus.query(self._expression)
        self._attr_available = result.error is None

        # Nuke value if sensor becomes unavailable
        if not self._attr_available:
            self._attr_is_on = None

        # Naive bool cast without template
        elif self._value_template is None:
            self._attr_is_on = bool(result.value)

        # Evaluate template
        else:
            render_result = self._value_template.async_render(
                variables={"value": result.value},
            )

            if render_result is not None:
                self._attr_is_on = bool(render_result)
            else:
                self._attr_is_on = None
