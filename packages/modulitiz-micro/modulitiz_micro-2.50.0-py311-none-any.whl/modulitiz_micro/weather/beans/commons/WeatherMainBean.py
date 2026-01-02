from dataclasses import dataclass


@dataclass
class WeatherMainBean:
	temp: float
	feels_like: float
	temp_min: float
	temp_max: float
	pressure: int
	sea_level: int
	humidity: int
	grnd_level: int
