# Prometheus sensor for Home Assistant

Use [PromQL expressions](https://prometheus.io/docs/prometheus/latest/querying/basics/) to query [Prometheus](https://prometheus.io/)-compatible APIs and expose the results as sensor values in [Home Assistant](https://www.home-assistant.io/).

Contributions welcome!

## Compatibility

Tested against Home Asisstant 2025.8.3.

## Options

[Device class (binary sensor)]: https://www.home-assistant.io/integrations/binary_sensor/#device-class
[Device class (sensor)]: https://www.home-assistant.io/integrations/sensor/#device-class
[PromQL]: https://prometheus.io/docs/prometheus/latest/querying/basics/
[State class]: https://developers.home-assistant.io/docs/core/entity/sensor/#available-state-classes
[Template]: https://www.home-assistant.io/docs/configuration/templating/
[Unique ID]: https://www.home-assistant.io/faq/unique_id/

### Binary Sensor

| Name                | Type   | Default  | Description                    |
|---------------------|--------|----------|--------------------------------|
| name                | string | required | Friendly name                  |
| unique_id           | string | optional | [Unique ID]                    |
| expr                | string | required | [PromQL] expression            |
| value_template      | string | optional | [Template]                     |
| device_class        | string | optional | [Device class (binary sensor)] |

The binary sensor uses a naive `bool()` cast on the value or, if configured, the
result of the template expression. This means that the sensor will be off, when
the query returns `0` or `0.0` and on in every other case.

### Sensor

| Name                | Type   | Default  | Description             |
|---------------------|--------|----------|-------------------------|
| name                | string | required | Friendly name           |
| unique_id           | string | optional | [Unique ID]             |
| expr                | string | required | [PromQL] expression     |
| unit_of_measurement | string | optional | Unit of the measurement |
| device_class        | string | optional | [Device class (sensor)] |
| state_class         | string | optional | [State class]           |

## Example usage

```yaml
binary_sensor:
  - platform: prometheus_sensor
    url: http://localhost:9090
    queries:
      - name: Front Door
        unique_id: front_door_open
        expr: front_door_open
        value_template: "{{ value == 1 }}"
        device_class: door

sensor:
  - platform: prometheus_sensor
    url: http://localhost:9090
    queries:
      - name: Energy usage
        expr: energy_usage_wh / 1000
        unit_of_measurement: kWh
        device_class: energy
        state_class: total_increasing
      - name: Energy solar production
        expr: energy_solar_wh / 1000
        unit_of_measurement: kWh
        device_class: energy
        state_class: total_increasing
      - name: Energy grid consumption
        unit_of_measurement: kWh
        expr: energy_grid_wh / 1000
        device_class: energy
        state_class: total_increasing
```

## Upstream integration

I tried to get this component merged into home-assistant in 2020/12.

<https://github.com/home-assistant/core/pull/44508>

That effort failed when the requirement to create a third party
library to handle the interaction with the Prometheus API came up.

The code is using async aiohttp calls and reuses the home-assistant
internal aiohttp client session.
At the time I did not find a ready to use async prometheus client
library, and the search for one wasn't easy due to the term `client`
being overloaded in the Prometheus world.
I was also not going to start maintaining such a library, when the
class to wrap the Prometheus instant query API was a mere 36 LoC.

Everyone is welcome to pick up this effort!
