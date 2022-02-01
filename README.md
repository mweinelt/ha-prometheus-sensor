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


