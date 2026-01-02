from modulitiz_nano.ModuloDate import ModuloDate


class TokenBean(object):
	def __init__(self,value:str):
		self.value=value
		self.dateInsert=ModuloDate.now()
	
	@staticmethod
	def fromDict(diz:dict):
		bean=TokenBean(diz["value"])
		bean.dateInsert=ModuloDate.timestampToDate(diz["dateInsert"])
		return bean
	
	def toDict(self)->dict:
		return {
			"value":self.value,
			"dateInsert":ModuloDate.dateToTimestamp(self.dateInsert)
		}
	
	def isExpired(self)->bool:
		return self.__diffDateInsert()>30
	
	def isTooEarly(self)->bool:
		return self.__diffDateInsert()<=2
	
	def __diffDateInsert(self)->int:
		return ModuloDate.minutesDiff(ModuloDate.now(),self.dateInsert)
