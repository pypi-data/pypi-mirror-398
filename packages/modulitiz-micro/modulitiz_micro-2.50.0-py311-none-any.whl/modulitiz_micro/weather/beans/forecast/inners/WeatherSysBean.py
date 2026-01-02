from dataclasses import dataclass


@dataclass
class WeatherSysBean:
	pod: str
	"""
	Part of the day (n - night, d - day)
	"""
