from montreal_aqi_api._internal.utils import get_version


def test_get_version_returns_string():
    version = get_version()
    assert isinstance(version, str)
    assert version != ""
