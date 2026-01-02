from modulitiz_micro.weather.AbstractModuleWeather import AbstractModuleWeather
from modulitiz_micro.weather.beans.current.WeatherCurrentDataBean import WeatherCurrentDataBean
from modulitiz_micro.weather.beans.forecast.WeatherForecastDataBean import WeatherForecastDataBean


class ModuleWeather(AbstractModuleWeather):
	"""
	Utility for current weather and forecasts.
	https://openweathermap.org/api
	"""
	
	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)
	
	def getCurrentByCoordinates(self,lat:float,lon:float)->WeatherCurrentDataBean|None:
		return self._getCurrent(lat,lon,None,None)
	
	def getCurrentByCity(self,city:str,codState:str)->WeatherCurrentDataBean|None:
		return self._getCurrent(None,None,city,codState)
	
	def getForecastByCoordinates(self,lat:float,lon:float)->WeatherForecastDataBean|None:
		return self._getForecast(lat,lon,None,None)
	
	def getForecastByCity(self,city:str,codState:str)->WeatherForecastDataBean|None:
		return self._getForecast(None,None,city,codState)
