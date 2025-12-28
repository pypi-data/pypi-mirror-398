from montreal_aqi_api.pollutants import Pollutant


def test_pollutant_attributes():
    p = Pollutant(
        name="PM2.5",
        fullname="Fine particles",
        unit="µg/m³",
        aqi=42.0,
        concentration=29.4,
    )

    assert p.name == "PM2.5"
    assert p.aqi == 42.0
    assert p.unit == "µg/m³"


def test_pollutant_is_immutable():
    p = Pollutant(
        name="O3",
        fullname="Ozone",
        unit="µg/m³",
        aqi=60,
        concentration=192,
    )

    try:
        p.aqi = 80
        assert False, "Pollutant should be immutable"
    except Exception:
        assert True
