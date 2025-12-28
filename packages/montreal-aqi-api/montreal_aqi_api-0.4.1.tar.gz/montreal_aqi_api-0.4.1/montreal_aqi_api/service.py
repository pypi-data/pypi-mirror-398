from __future__ import annotations

import logging
from datetime import date
from typing import Any, Mapping

from montreal_aqi_api._internal.parsing import parse_pollutants
from montreal_aqi_api.api import fetch_latest_station_records, fetch_open_stations
from montreal_aqi_api.station import Station

logger = logging.getLogger(__name__)


def _parse_station_metadata(record: Mapping[str, Any]) -> tuple[date, int] | None:
    """
    Extract and validate date and hour from a raw station record.
    """
    raw_date = record.get("date")
    raw_hour = record.get("heure")

    if not isinstance(raw_date, str):
        return None
    if not isinstance(raw_hour, (int, str)):
        return None

    try:
        parsed_date = date.fromisoformat(raw_date)
        parsed_hour = int(raw_hour)
    except ValueError:
        return None

    return parsed_date, parsed_hour


def get_station_aqi(station_id: str) -> Station | None:
    """
    Return the latest AQI data for a given station.
    """
    records = fetch_latest_station_records(station_id)
    if not records:
        logger.info("No records found for station %s", station_id)
        return None

    pollutants = parse_pollutants(records)
    if not pollutants:
        logger.info("No pollutants parsed for station %s", station_id)
        return None

    metadata = _parse_station_metadata(records[0])
    if metadata is None:
        logger.warning("Invalid station metadata for station %s", station_id)
        return None

    station_date, hour = metadata

    station = Station(
        station_id=station_id,
        date=station_date,
        hour=hour,
        pollutants=pollutants,
    )

    logger.info(
        "Station %s AQI=%d dominant=%s",
        station_id,
        round(station.aqi),
        station.main_pollutant.name,
    )

    return station


def list_open_stations() -> list[dict[str, Any]]:
    """
    List all currently open monitoring stations.
    """
    return fetch_open_stations()
