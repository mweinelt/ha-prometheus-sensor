# Prometheus sensor for Home Assistant

Query latest values from prometheus metrics and import them as as sensors into home assistant.

Contributions welcome!

## Compatibility

Tested with Home Assistant 2021.12.10.

## Todos

- Migrate to `DataUpdateCoordinator` (https://developers.home-assistant.io/docs/integration_fetching_data/)

## Example usage

```yaml
sensor:
  - platform: prometheus_query
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

https://github.com/home-assistant/core/pull/44508

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
