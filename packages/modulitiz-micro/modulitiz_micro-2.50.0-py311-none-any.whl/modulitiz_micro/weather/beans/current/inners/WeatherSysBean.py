from dataclasses import dataclass


@dataclass
class WeatherSysBean:
	type: int
	id: int
	country: str
	sunrise: int
	sunset: int
