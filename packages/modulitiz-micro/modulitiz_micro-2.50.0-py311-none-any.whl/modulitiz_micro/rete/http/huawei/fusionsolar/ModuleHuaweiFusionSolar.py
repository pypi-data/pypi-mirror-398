from modulitiz_micro.rete.http.huawei.fusionsolar.beans.device.DeviceBean import DeviceBean
from modulitiz_micro.rete.http.huawei.fusionsolar.beans.device.DeviceDataBattery import DeviceDataBattery
from modulitiz_micro.rete.http.huawei.fusionsolar.beans.device.DeviceDataPowerSensor import DeviceDataPowerSensor
from modulitiz_micro.rete.http.huawei.fusionsolar.beans.device.DeviceDataResidentialInverter import DeviceDataResidentialInverter
from modulitiz_micro.rete.http.huawei.fusionsolar.enums.DevTypeIdEnum import DevTypeIdEnum
from modulitiz_micro.rete.http.huawei.fusionsolar.service.AbstractHuaweiFusionSolar import AbstractHuaweiFusionSolar
from modulitiz_nano.exceptions.ExceptionNoData import ExceptionNoData


class ModuleHuaweiFusionSolar(AbstractHuaweiFusionSolar):
	"""
	Api reference:
	https://support.huawei.com/enterprise/en/doc/EDOC1100465337/3055b7a9/api-reference
	"""
	URL_PREFIX="https://eu5.fusionsolar.huawei.com/thirdData/"
	XSRF_TOKEN="XSRF-TOKEN"
	
	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)
		self.__plantCode:str|None=None
		self.__deviceIds:list[DeviceBean]=[]
	
	# TODO: @override
	def populate(self):
		super().populate()
		# load data
		self.__plantCode=self.getPlantCode()
		self.__deviceIds=self.getDeviceIds()
	
	#
	# plants
	#
	def getPlants(self)->dict:
		return self._makeGenericRequest("stations", {"pageNo": 1})
	
	def getPlantCode(self)->str:
		if self.__plantCode is not None:
			return self.__plantCode
		self.__plantCode = self.getPlants()['list'][0]['plantCode']
		return self.__plantCode
	
	def getRealtimePlantData(self)->dict:
		return self._makeGenericRequest("getStationRealKpi",{"stationCodes":self.__plantCode})[0]["dataItemMap"]
	
	#
	# device
	#
	def getDevices(self)->list:
		return list(self._makeGenericRequest("getDevList",{"stationCodes":self.__plantCode}))
	
	def getDeviceIds(self)->list[DeviceBean]:
		if self.__deviceIds:
			return self.__deviceIds
		self.__deviceIds = [DeviceBean(x["id"],x["devTypeId"]) for x in self.getDevices()]
		return self.__deviceIds
	
	#
	# realtime data
	#
	def getRealtimeDataBattery(self)->DeviceDataBattery:
		return DeviceDataBattery(**self.__getRealtimeDeviceData(DevTypeIdEnum.BATTERY,True))
	
	def getRealtimeProductionWh(self) -> int:
		"""
		Get total realtime production in Wh.
		"""
		results=self.getRealtimeDataResidentialInverter()
		whProductions=[x.pv1_u*x.pv1_i for x in results]
		return int(sum(whProductions))
	
	def getRealtimeDataResidentialInverter(self)->list[DeviceDataResidentialInverter]:
		elems=[]
		for x in self.__getRealtimeDeviceData(DevTypeIdEnum.RESIDENTIAL_INVERTER,False):
			elems.append(DeviceDataResidentialInverter(**x))
		return elems
	
	def getRealtimeDataPowerSensor(self)->DeviceDataPowerSensor:
		return DeviceDataPowerSensor(**self.__getRealtimeDeviceData(DevTypeIdEnum.POWER_SENSOR,True))
	
	def __getRealtimeDeviceData(self,devTypeId:DevTypeIdEnum,getOnlyFirstResult:bool)->dict|list:
		devIds=",".join([str(x.idDevice) for x in self.__deviceIds if x.idType==devTypeId])
		response=self._makeGenericRequest("getDevRealKpi",{"devIds":devIds,"devTypeId":devTypeId})
		if getOnlyFirstResult:
			try:
				output = response[0]["dataItemMap"]
			except IndexError as ex:
				raise ExceptionNoData("Error parsing response: "+str(response)) from ex
			return output
		return [x["dataItemMap"] for x in response]
