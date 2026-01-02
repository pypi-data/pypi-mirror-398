from dataclasses import dataclass


@dataclass
class WeatherWindBean:
	speed: float
	deg: int
	gust: int|None = None
