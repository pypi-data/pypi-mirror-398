from montreal_aqi_api.pollutants import Pollutant
from montreal_aqi_api.station import Station


def _pollutant(name: str, aqi: float) -> Pollutant:
    return Pollutant(
        name=name,
        fullname=name,
        unit="µg/m³",
        aqi=aqi,
        concentration=aqi,
    )


def test_station_aqi_is_max_pollutant():
    station = Station(
        station_id="3",
        date="2025-01-01",
        hour=14,
        pollutants={
            "PM2.5": _pollutant("PM2.5", 45),
            "O3": _pollutant("O3", 62),
        },
    )

    assert station.aqi == 62


def test_station_main_pollutant():
    station = Station(
        station_id="3",
        date="2025-01-01",
        hour=14,
        pollutants={
            "NO2": _pollutant("NO2", 30),
            "PM2.5": _pollutant("PM2.5", 55),
        },
    )

    assert station.main_pollutant.name == "PM2.5"
