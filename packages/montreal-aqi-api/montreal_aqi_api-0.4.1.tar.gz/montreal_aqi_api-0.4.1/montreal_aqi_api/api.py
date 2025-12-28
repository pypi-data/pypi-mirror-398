from __future__ import annotations

import logging
from typing import Any, Dict, List, Union

import requests

from montreal_aqi_api.config import (
    API_URL,
    RESID_IQA_PAR_STATION_EN_TEMPS_REEL,
    RESID_LIST,
)

logger = logging.getLogger(__name__)

# Type explicite pour les paramètres HTTP acceptés par requests
Params = Dict[str, Union[str, int, float]]


def _fetch(resource_id: str) -> List[Dict[str, Any]]:
    """
    Fetch raw records from the Montreal open data API for a given resource.
    """
    logger.info(
        "Fetching data from Montreal open data API (resource_id=%s)", resource_id
    )

    params: Params = {
        "resource_id": resource_id,
        "limit": 1000,
    }

    response = requests.get(API_URL, params=params, timeout=10)
    response.raise_for_status()

    payload = response.json()
    records = payload.get("result", {}).get("records", [])

    if not isinstance(records, list):
        logger.warning("Unexpected API response format")
        return []

    logger.debug("Retrieved %d records", len(records))
    return records


def fetch_latest_station_records(station_id: str) -> List[Dict[str, Any]]:
    """
    Return the latest available records for a given station ID.
    """
    records = _fetch(RESID_IQA_PAR_STATION_EN_TEMPS_REEL)

    station_records = [
        r
        for r in records
        if isinstance(r.get("stationId"), str) and r.get("stationId") == station_id
    ]

    if not station_records:
        logger.warning("No records found for station %s", station_id)
        return []

    try:
        latest_hour = max(int(r["heure"]) for r in station_records)
    except (KeyError, ValueError, TypeError):
        logger.warning("Invalid 'heure' field in station records for %s", station_id)
        return []

    latest_records = [
        r for r in station_records if int(r.get("heure", -1)) == latest_hour
    ]

    logger.debug(
        "Found %d records for station %s at hour %s",
        len(latest_records),
        station_id,
        latest_hour,
    )

    return latest_records


def fetch_open_stations() -> List[Dict[str, Any]]:
    """
    Return a list of currently open monitoring stations.
    """
    records = _fetch(RESID_LIST)

    stations: List[Dict[str, Any]] = []

    for r in records:
        if r.get("statut") != "ouvert":
            continue

        stations.append(
            {
                "station_id": r.get("numero_station"),
                "name": r.get("nom"),
                "address": r.get("adresse"),
                "borough": r.get("arrondissement_ville"),
            }
        )

    logger.info("Found %d open stations", len(stations))
    return stations
