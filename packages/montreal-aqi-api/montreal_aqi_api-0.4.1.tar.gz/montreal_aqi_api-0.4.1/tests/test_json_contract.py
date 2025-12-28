import json

from tests._schemas import validate_contract


def test_error_payload_contract():
    payload = {
        "version": "1",
        "type": "error",
        "error": {
            "code": "NO_DATA",
            "message": "No data available for this station",
        },
    }

    validate_contract(payload)


def test_station_list_payload_contract():
    payload = {
        "version": "1",
        "type": "stations",
        "stations": [
            {
                "station_id": "80",
                "name": "Saint-Joseph",
                "borough": "Rosemont-La Petite-Patrie",
            }
        ],
    }

    validate_contract(payload)


def test_station_aqi_payload_contract():
    payload = {
        "version": "1",
        "type": "station",
        "station_id": "80",
        "date": "2025-12-18",
        "hour": 16,
        "aqi": 49,
        "dominant_pollutant": "PM2.5",
        "pollutants": {
            "PM2.5": {
                "name": "PM2.5",
                "aqi": 49,
                "concentration": 34.3,
            },
            "O3": {
                "name": "O3",
                "aqi": 22,
                "concentration": 70.4,
            },
        },
    }

    validate_contract(payload)


def test_cli_output_respects_contract(capsys, monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        ["montreal-aqi", "--station", "80"],
    )

    from montreal_aqi_api.cli import main

    main()

    out, _ = capsys.readouterr()
    payload = json.loads(out)

    validate_contract(payload)
