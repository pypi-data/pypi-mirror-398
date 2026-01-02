from modulitiz_micro.weather.beans.commons.WeatherCoordBean import WeatherCoordBean


class WeatherCityBean(object):
	def __init__(self,data: dict):
		self.id: int=data["id"]
		self.name: str=data["name"]
		self.coord = WeatherCoordBean(**data["coord"])
		self.country: str=data["country"]
		self.population: int=data["population"]
		self.timezone: int=data["timezone"]
		self.sunrise: int=data["sunrise"]
		self.sunset: int=data["sunset"]
