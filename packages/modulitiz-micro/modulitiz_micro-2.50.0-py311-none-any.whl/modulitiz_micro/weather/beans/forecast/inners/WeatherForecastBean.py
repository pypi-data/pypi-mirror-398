from datetime import datetime

from modulitiz_micro.weather.beans.commons.WeatherBean import WeatherBean
from modulitiz_micro.weather.beans.commons.WeatherCloudsBean import WeatherCloudsBean
from modulitiz_micro.weather.beans.commons.WeatherRainBean import WeatherRainBean
from modulitiz_micro.weather.beans.commons.WeatherWindBean import WeatherWindBean
from modulitiz_micro.weather.beans.forecast.inners.WeatherMainForecastBean import WeatherMainForecastBean
from modulitiz_micro.weather.beans.forecast.inners.WeatherSysBean import WeatherSysBean
from modulitiz_nano.ModuloDate import ModuloDate


class WeatherForecastBean(object):
	def __init__(self,data: dict):
		dtUtc=ModuloDate.timestampUtcToDate(data["dt"])
		dtLocal=ModuloDate.setTimezoneLocal(dtUtc)
		self.dt: datetime=ModuloDate.removeTimezoneInfo(dtLocal)
		self.main = WeatherMainForecastBean(**data["main"])
		self.weather=[WeatherBean(**w) for w in data.get("weather",[])]
		self.clouds=WeatherCloudsBean(**data["clouds"])
		self.wind=WeatherWindBean(**data["wind"])
		self.visibility: int=data["visibility"]
		
		self.pop: float=data["pop"]
		"""
		Probability of precipitation.
		Vary between 0 and 1, where 0 is equal to 0%, 1 is equal to 100%
		"""
		
		self.rain=WeatherRainBean(data.get("rain",{}))
		self.sys=WeatherSysBean(**data["sys"])
		self.dt_txt: str=data["dt_txt"]
