from modulitiz_micro.weather.beans.AbstractWeatherDataBean import AbstractWeatherDataBean
from modulitiz_micro.weather.beans.forecast.inners.WeatherCityBean import WeatherCityBean
from modulitiz_micro.weather.beans.forecast.inners.WeatherForecastBean import WeatherForecastBean


class WeatherForecastDataBean(AbstractWeatherDataBean):
	def __init__(self, *args,**kwargs):
		super().__init__(*args,**kwargs)
		self.message: int=self._data["message"]
		self.cnt: int=self._data["cnt"]
		self.list = [WeatherForecastBean(w) for w in self._data.get("list", [])]
		self.city = WeatherCityBean(self._data["city"])
