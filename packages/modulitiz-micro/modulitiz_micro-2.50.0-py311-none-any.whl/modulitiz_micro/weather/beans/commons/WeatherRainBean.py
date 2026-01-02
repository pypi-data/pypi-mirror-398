class WeatherRainBean(object):
	
	def __init__(self,data:dict):
		self.h1:float|None=data.get("1h",None)
		self.h3:float|None=data.get("3h",None)
