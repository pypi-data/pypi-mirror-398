# AQI monitoring for the city of Montréal (Québec, Canada)

![Latest Release](https://img.shields.io/github/v/release/normcyr/montreal-aqi-api?label=version)
![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)
[![CI](https://github.com/normcyr/montreal-aqi-api/actions/workflows/ci.yml/badge.svg)](https://github.com/normcyr/montreal-aqi-api/actions/workflows/ci.yml)
![PyPI](https://img.shields.io/pypi/v/montreal-aqi-api)
![Downloads](https://img.shields.io/pypi/dm/montreal-aqi-api)
![License](https://img.shields.io/github/license/normcyr/montreal-aqi-api)

A Python library and CLI tool to fetch, process, and expose air quality index (AQI) data from the City of Montréal open data platform.

The project is designed to be:

- **scriptable** (JSON output by default)
- **embeddable** as a Python library
- suitable for **automation** (Home Assistant, cron jobs, data pipelines)

---

## Features

- Fetches the latest air quality data from Montréal’s open data portal
- Lists currently active air quality monitoring stations
- Computes the AQI based on RSQA methodology
- Estimates pollutant concentrations from reported AQI contributions¹
- Exposes structured station and pollutant data via Python models
- Outputs **machine-readable JSON** from the CLI
- Structured logging with optional debug mode
- Test suite covering core logic, JSON contract, and CLI behavior

¹ Estimated concentrations are derived from rounded AQI values and should be treated as approximations.

---

## Requirements

- Python 3.11 or newer
- `requests`

---

## Installation

### From PyPI (recommended)

```bash
pip install montreal-aqi-api
```

### From source

```bash
git clone https://github.com/normcyr/montreal-aqi-api.git
cd montreal-aqi-api
python3 -m venv venv
source venv/bin/activate
pip install .
```

---

## CLI Usage

The CLI **always outputs JSON on stdout**. Logs and diagnostics are written to **stderr**.

### Fetch AQI for a specific station

```bash
montreal-aqi --station <station_id>
```

### List available monitoring stations

```bash
montreal-aqi --list
```

### Enable debug logging

```bash
montreal-aqi --station <station_id> --debug
```

### Print the JSON in a pretty format

```bash
montreal-aqi --station <station_id> --pretty
```

or

```bash
montreal-aqi --list --pretty
```

### No arguments

If no arguments are provided, the CLI returns a JSON error payload. Interactive prompts are intentionally avoided to keep behavior predictable in automated environments.

---

## Integrations

This library is designed to be consumed by automated systems and integrations.

### Home Assistant

Used by the custom Home Assistant integration:

- https://github.com/normcyr/home-assistant-montreal-aqi

### Other Use Cases

- Cron jobs
- Data ingestion pipelines
- Monitoring dashboards
- Research / environmental analysis

---

## JSON Contract — Version 1 (Frozen)

As of **v0.4.0**, the JSON output contract is **explicitly versioned and frozen**. The output format is formally specified in:
[docs/json_contract_v1.md](docs/json_contract_v1.md).

The JSON output is governed by the official JSON Schema v1 and all payloads include:

```json
{
  "version": 1,
  "type": "..."
}
```

### Error Payload

```json
{
  "version": 1,
  "type": "error",
  "error": {
    "code": "NO_DATA",
    "message": "No data available for this station"
  }
}
```

### Stations List Payload

```json
{
  "version": 1,
  "type": "stations",
  "stations": [
    {
      "station_id": "3",
      "name": "Saint-Jean-Baptiste",
      "borough": "Rivière-des-Prairies"
    }
  ]
}
```

### Station AQI Payload

```json
{
  "version": 1,
  "type": "station",
  "station_id": "80",
  "date": "2025-08-08",
  "hour": 10,
  "aqi": 49,
  "dominant_pollutant": "PM2.5",
  "pollutants": {
    "PM2.5": {
      "name": "PM2.5",
      "aqi": 49,
      "concentration": 34.3
    },
    "O3": {
      "name": "O3",
      "aqi": 22,
      "concentration": 70.4
    }
  }
}
```

---

## Python Usage

```python
from montreal_aqi_api.service import get_station_aqi

station = get_station_aqi("80")
if station:
    print(station.to_dict())
```

Domain objects (`Station`, `Pollutant`) expose explicit serialization helpers
to ease downstream usage.

---

## AQI Methodology

AQI values follow the methodology defined by the
[Réseau de surveillance de la qualité de l’air (RSQA)](https://donnees.montreal.ca/dataset/rsqa-indice-qualite-air).

### Reference Values

| Pollutant | Full Name            | Reference |
|-----------|----------------------|-----------|
| SO₂       | Sulfur Dioxide       | 500 µg/m³ |
| CO        | Carbon Monoxide      | 35 mg/m³  |
| O₃        | Ozone                | 160 µg/m³ |
| NO₂       | Nitrogen Dioxide     | 400 µg/m³ |
| PM2.5     | Particulate Matter   | 35 µg/m³  |

---

## Project Status

- JSON contract v1 frozen and validated by tests
- Suitable for automation and integration
- API stability guaranteed within v1

---

## Contributing

Contributions are welcome.

Please ensure that:

- tests pass (`pytest`)
- the JSON contract remains backward compatible
- any change affecting output is covered by tests

Open an issue before proposing breaking changes.

---

## Data Source

Data is retrieved from the
[Ville de Montréal Open Data Portal](https://donnees.montreal.ca/fr/dataset/rsqa-indice-qualite-air).

---

## License

This project is licensed under the [MIT License](LICENSE).
