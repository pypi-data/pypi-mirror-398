from dataclasses import dataclass

from modulitiz_micro.weather.enums.IdWeatherEnum import IdWeatherEnum


@dataclass
class WeatherBean:
	id: IdWeatherEnum
	main: str
	description: str
	icon: str
