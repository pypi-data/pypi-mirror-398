from modulitiz_micro.weather.beans.AbstractWeatherDataBean import AbstractWeatherDataBean
from modulitiz_micro.weather.beans.commons.WeatherBean import WeatherBean
from modulitiz_micro.weather.beans.commons.WeatherCloudsBean import WeatherCloudsBean
from modulitiz_micro.weather.beans.commons.WeatherCoordBean import WeatherCoordBean
from modulitiz_micro.weather.beans.commons.WeatherMainBean import WeatherMainBean
from modulitiz_micro.weather.beans.commons.WeatherRainBean import WeatherRainBean
from modulitiz_micro.weather.beans.commons.WeatherWindBean import WeatherWindBean
from modulitiz_micro.weather.beans.current.inners.WeatherSysBean import WeatherSysBean
from modulitiz_micro.weather.enums.IdWeatherEnum import IdWeatherEnum


class WeatherCurrentDataBean(AbstractWeatherDataBean):
	def __init__(self, *args,**kwargs):
		super().__init__(*args,**kwargs)
		self.coord = WeatherCoordBean(**self._data["coord"])
		self.weather = [WeatherBean(**w) for w in self._data.get("weather", [])]
		self.base: str=self._data.get("base", "")
		self.main = WeatherMainBean(**self._data["main"])
		self.visibility: int=self._data["visibility"]
		self.wind = WeatherWindBean(**self._data["wind"])
		self.rain = WeatherRainBean(self._data.get("rain",{}))
		self.clouds = WeatherCloudsBean(**self._data["clouds"])
		self.dt: int=self._data["dt"]
		self.sys = WeatherSysBean(**self._data["sys"])
		self.timezone: int=self._data["timezone"]
		self.id: int=self._data["id"]
		self.name: str=self._data["name"]
	
	def isClearSky(self) -> bool:
		return self.weather[0].id==IdWeatherEnum.CLEAR_SKY
