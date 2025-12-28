CONTRACT_VERSION: str = "1"

API_URL = "https://donnees.montreal.ca/api/3/action/datastore_search"

RESID_LIST = "29db5545-89a4-4e4a-9e95-05aa6dc2fd80"
RESID_IQA_PAR_STATION_EN_TEMPS_REEL = "f4eca3bf-5ded-4d3c-a8dc-ed42486498f3"

POLLUTANT_ALIASES = {
    "PM": "PM2.5",
}

REFERENCE_VALUES = {
    "SO2": {"fullname": "sulfur dioxide", "ref": 500.0, "unit": "µg/m3"},
    "CO": {"fullname": "carbon monoxide", "ref": 35.0, "unit": "mg/m3"},
    "O3": {"fullname": "ozone", "ref": 160.0, "unit": "µg/m3"},
    "NO2": {"fullname": "nitrogen dioxide", "ref": 400.0, "unit": "µg/m3"},
    "PM2.5": {"fullname": "particulate matter PM2.5", "ref": 35.0, "unit": "µg/m3"},
}
