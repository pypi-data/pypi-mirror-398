from abc import ABC


class AbstractWeatherDataBean(ABC):
	def __init__(self, data: dict):
		self._data=data
		self.cod: int=int(data["cod"])
