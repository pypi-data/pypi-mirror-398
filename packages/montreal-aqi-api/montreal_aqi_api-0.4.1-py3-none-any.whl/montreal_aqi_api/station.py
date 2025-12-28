from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Dict

from montreal_aqi_api.pollutants import Pollutant


@dataclass(slots=True)
class Station:
    station_id: str
    date: date
    hour: int
    pollutants: Dict[str, Pollutant]

    @property
    def aqi(self) -> int:
        return max(p.aqi for p in self.pollutants.values())

    @property
    def main_pollutant(self) -> Pollutant:
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
                    "concentration": float(p.concentration),
                }
                for code, p in self.pollutants.items()
            },
        }
