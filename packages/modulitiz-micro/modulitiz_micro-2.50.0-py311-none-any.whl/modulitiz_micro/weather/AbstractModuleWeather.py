import json
from abc import ABC
from typing import Type

from modulitiz_micro.exceptions.http.ExceptionHttpGeneric import ExceptionHttpGeneric
from modulitiz_micro.files.cache.decorators.cacheRam import cacheRam
from modulitiz_micro.rete.http.ModuloHttp import ModuloHttp
from modulitiz_micro.rete.http.ModuloHttpUtils import ModuloHttpUtils
from modulitiz_micro.weather.beans.AbstractWeatherDataBean import AbstractWeatherDataBean
from modulitiz_micro.weather.beans.current.WeatherCurrentDataBean import WeatherCurrentDataBean
from modulitiz_micro.weather.beans.forecast.WeatherForecastDataBean import WeatherForecastDataBean
from modulitiz_nano.exceptions.ExceptionRuntime import ExceptionRuntime
from modulitiz_nano.files.ModuloLogging import ModuloLogging


class AbstractModuleWeather(ABC):
	OPTIONS="lang=it&units=metric"
	KEY="appid=e28cd365c35c12e3ed8f2d84e04398c9"
	
	__BASE_URL="https://api.openweathermap.org/data/"
	URL_CURRENT="2.5/weather"
	URL_FORECAST="2.5/forecast"
	
	def __init__(self,logger:ModuloLogging):
		self._logger=logger
	
	def _getCurrent(self,lat:float|None,lon:float|None,city:str|None,codState:str|None)-> WeatherCurrentDataBean|None:
		return self.__makeGenericRequest(self.URL_CURRENT,WeatherCurrentDataBean,lat,lon,city,codState)
	
	def _getForecast(self,lat:float|None,lon:float|None,city:str|None,codState:str|None)->WeatherForecastDataBean|None:
		return self.__makeGenericRequest(self.URL_FORECAST,WeatherForecastDataBean,lat,lon,city,codState)
	
	@staticmethod
	def __addOptionCoordinates(lat:float,lon:float)->str:
		return f"&lat={lat}&lon={lon}"
	@staticmethod
	def __addOptionCity(city:str,codState:str)->str:
		return "&q="+ModuloHttpUtils.encodeUrl(f"{city},{codState}")
	
	@cacheRam(1)
	def __makeGenericRequest(self,baseUrl:str,classResponseBean:Type[AbstractWeatherDataBean],
			lat:float|None,lon:float|None,city:str|None,codState:str|None)-> Type[AbstractWeatherDataBean]|None:
		if lat is not None and lon is not None:
			options=self.__addOptionCoordinates(lat,lon)
		elif city is not None and codState is not None:
			options=self.__addOptionCity(city,codState)
		else:
			raise ExceptionRuntime("Wrong options")
		# url
		url=self.__BASE_URL+baseUrl+f"?{self.OPTIONS}&{self.KEY}"+options
		http=ModuloHttp(url,self._logger,False)
		try:
			response=http.doGet(0,False)
		except ExceptionHttpGeneric:
			return None
		# process response
		responseJson = json.loads(response.responseBody)
		return classResponseBean(responseJson)
