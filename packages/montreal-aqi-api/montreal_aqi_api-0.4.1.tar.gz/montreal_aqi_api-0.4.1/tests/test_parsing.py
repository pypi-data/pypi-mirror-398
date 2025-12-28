from montreal_aqi_api._internal.parsing import parse_pollutants


def test_parse_pollutants_basic():
    """
    Basic parsing of known pollutants with valid AQI values.
    """
    records = [
        {
            "pollutant": "PM2.5",
            "valeur": "50",
            "heure": "13",
        },
        {
            "pollutant": "O3",
            "valeur": "25",
            "heure": "13",
        },
    ]

    pollutants = parse_pollutants(records)

    assert "PM2.5" in pollutants
    assert "O3" in pollutants

    pm25 = pollutants["PM2.5"]
    assert pm25.aqi == 50
    assert pm25.concentration > 0
    assert pm25.unit

    o3 = pollutants["O3"]
    assert o3.aqi == 25
    assert o3.concentration > 0


def test_parse_pollutants_accepts_numeric_strings():
    """
    AQI values provided as strings should be accepted.
    """
    records = [
        {
            "pollutant": "NO2",
            "valeur": "10",
            "heure": "08",
        }
    ]

    pollutants = parse_pollutants(records)

    assert "NO2" in pollutants
    assert pollutants["NO2"].aqi == 10


def test_parse_pollutants_ignores_unknown_pollutants():
    """
    Unknown pollutant codes should be ignored.
    """
    records = [
        {
            "pollutant": "XYZ",
            "valeur": "100",
            "heure": "12",
        }
    ]

    pollutants = parse_pollutants(records)

    assert pollutants == {}


def test_parse_pollutants_ignores_invalid_records():
    """
    Records missing required fields or with invalid types are ignored.
    """
    records = [
        {"pollutant": "PM2.5"},  # missing value
        {"valeur": "30"},  # missing pollutant
        {"pollutant": "O3", "valeur": None},
        {"pollutant": 123, "valeur": "10"},
    ]

    pollutants = parse_pollutants(records)

    assert pollutants == {}


def test_parse_pollutants_normalizes_aliases():
    """
    Pollutant aliases (e.g. PM → PM2.5) should be normalized.
    """
    records = [
        {
            "pollutant": "PM",
            "valeur": "40",
            "heure": "14",
        }
    ]

    pollutants = parse_pollutants(records)

    assert "PM2.5" in pollutants
    assert pollutants["PM2.5"].aqi == 40
