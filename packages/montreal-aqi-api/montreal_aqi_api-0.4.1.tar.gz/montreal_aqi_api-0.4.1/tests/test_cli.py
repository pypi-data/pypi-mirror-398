from __future__ import annotations

import json
import sys
from unittest.mock import patch

import pytest

from montreal_aqi_api.cli import main

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _FakePollutant:
    def __init__(self, name: str, aqi: float, concentration: float | None = None):
        self.name = name
        self.aqi = aqi
        self.concentration = concentration


class _FakeStation:
    def __init__(self) -> None:
        self.station_id = "3"
        self.date = __import__("datetime").date(2025, 12, 18)
        self.hour = 16
        self.pollutants = {
            "PM2.5": _FakePollutant("PM2.5", 42.3, 12.1),
            "NO2": _FakePollutant("NO2", 18.7),
        }

    @property
    def aqi(self) -> float:
        return max(p.aqi for p in self.pollutants.values())

    @property
    def main_pollutant(self):
        return max(self.pollutants.values(), key=lambda p: p.aqi)

    def to_dict(self) -> dict[str, object]:
        return {
            "station_id": self.station_id,
            "date": self.date.isoformat(),
            "hour": self.hour,
            "aqi": round(self.aqi),
            "dominant_pollutant": self.main_pollutant.name,
            "pollutants": {
                code: {
                    "name": p.name,
                    "aqi": round(p.aqi),
                    **(
                        {"concentration": p.concentration}
                        if p.concentration is not None
                        else {}
                    ),
                }
                for code, p in self.pollutants.items()
            },
        }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_cli_no_arguments(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["montreal-aqi"])
    main()

    out, _ = capsys.readouterr()
    data = json.loads(out)

    assert data["version"] == "1"
    assert data["type"] == "error"
    assert data["error"]["code"] == "NO_ARGUMENTS"


@patch("montreal_aqi_api.cli.list_open_stations")
def test_cli_list_stations(mock_list, monkeypatch, capsys):
    mock_list.return_value = [
        {"station_id": "1", "name": "Station A", "borough": "A"},
        {"station_id": "2", "name": "Station B", "borough": "B"},
    ]

    monkeypatch.setattr(sys, "argv", ["montreal-aqi", "--list"])
    main()

    out, _ = capsys.readouterr()
    data = json.loads(out)

    assert data["version"] == "1"
    assert data["type"] == "stations"
    assert isinstance(data["stations"], list)
    assert len(data["stations"]) == 2


@patch("montreal_aqi_api.cli.get_station_aqi")
def test_cli_station_ok(mock_get, monkeypatch, capsys):
    mock_get.return_value = _FakeStation()

    monkeypatch.setattr(sys, "argv", ["montreal-aqi", "--station", "3"])
    main()

    out, _ = capsys.readouterr()
    data = json.loads(out)

    assert data["version"] == "1"
    assert data["type"] == "station"
    assert data["station_id"] == "3"
    assert "pollutants" in data
    assert "PM2.5" in data["pollutants"]


@patch("montreal_aqi_api.cli.get_station_aqi")
def test_cli_station_no_data(mock_get, monkeypatch, capsys):
    mock_get.return_value = None

    monkeypatch.setattr(sys, "argv", ["montreal-aqi", "--station", "999"])
    main()

    out, _ = capsys.readouterr()
    data = json.loads(out)

    assert data["version"] == "1"
    assert data["type"] == "error"
    assert data["error"]["code"] == "NO_DATA"


@patch("montreal_aqi_api.cli.get_station_aqi")
def test_cli_debug_flag(mock_get, monkeypatch, capsys):
    mock_get.return_value = _FakeStation()

    monkeypatch.setattr(
        sys,
        "argv",
        ["montreal-aqi", "--station", "3", "--debug"],
    )
    main()

    out, _ = capsys.readouterr()
    data = json.loads(out)

    assert data["type"] == "station"
