from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Union


@dataclass(frozen=True, slots=True)
class Pollutant:
    name: str
    fullname: str
    unit: str
    aqi: int
    concentration: float

    def to_dict(self) -> Dict[str, Union[str, int, float]]:
        return {
            "name": self.name,
            "concentration": self.concentration,
            "aqi": self.aqi,
        }
