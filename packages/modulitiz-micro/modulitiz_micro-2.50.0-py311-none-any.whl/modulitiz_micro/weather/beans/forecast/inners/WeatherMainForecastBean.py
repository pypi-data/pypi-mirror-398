from dataclasses import dataclass

from modulitiz_micro.weather.beans.commons.WeatherMainBean import WeatherMainBean


@dataclass
class WeatherMainForecastBean(WeatherMainBean):
	temp_kf: float
