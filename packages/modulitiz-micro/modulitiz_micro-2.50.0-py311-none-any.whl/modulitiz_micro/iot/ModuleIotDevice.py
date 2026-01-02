from modulitiz_micro.exceptions.http.ExceptionHttp import ExceptionHttp
from modulitiz_micro.iot.beans.IotDeviceBean import IotDeviceBean
from modulitiz_micro.iot.enums.IotOSEnum import IotOSEnum
from modulitiz_micro.iot.espurna.ModuleEspurna import ModuleEspurna
from modulitiz_micro.rete.http.ModuloHttp import ModuloHttp
from modulitiz_nano.ModuloNumeri import ModuloNumeri
from modulitiz_nano.ModuloStringhe import ModuloStringhe
from modulitiz_nano.exceptions.ExceptionRuntime import ExceptionRuntime
from modulitiz_nano.files.ModuloLogging import ModuloLogging


class ModuleIotDevice(object):
	def __init__(self, logger:ModuloLogging|None, deviceBean:IotDeviceBean):
		self.__logger=logger
		self.__deviceBean=deviceBean
	
	def getRelayStatus(self, relayNum:int)->bool:
		"""
		@param relayNum: Depending on which OS you choose, can be relative (0, 1, ...) or GPIO
		"""
		if self.__deviceBean.os==IotOSEnum.ESPURNA:
			url=ModuleEspurna.URL_GET_RELAY.format(ip=self.__deviceBean.ip,relayNum=relayNum,apiKey=self.__deviceBean.key)
		else:
			raise ExceptionRuntime("Iot os '%s' not known"%(self.__deviceBean.os,))
		return ModuloNumeri.intToBool(ModuloNumeri.strToInt(self.__sendRequest(url)))
	
	def setRelayStatus(self,relayNum: int,status: bool):
		"""
		@param relayNum: Depending on which OS you choose, can be relative (0, 1, ...) or GPIO
		@param status: value to set, can only be false or true
		"""
		self.__setRelayStatus(relayNum,status)
	
	def setRelayStatusToggle(self,relayNum: int):
		self.__setRelayStatus(relayNum,None)
	
	def __setRelayStatus(self, relayNum:int, status:bool|None):
		"""
		@param relayNum: Depending on which OS you choose, can be relative (0, 1, ...) or GPIO
		@param status: value to set, can be: false = off, true = on, null/None = toggle
		"""
		if self.__deviceBean.os==IotOSEnum.ESPURNA:
			if status is not None:
				statusStr=str(ModuloNumeri.boolToInt(status))
			else:
				statusStr=2
			url=ModuleEspurna.URL_SET_RELAY.format(ip=self.__deviceBean.ip,relayNum=relayNum,apiKey=self.__deviceBean.key,status=statusStr)
		else:
			raise ExceptionRuntime("Iot os '%s' not known"%(self.__deviceBean.os,))
		# check output
		statusOutput=ModuloNumeri.intToBool(int(self.__sendRequest(url)))
		if status is None or status==statusOutput:
			return
		raise ExceptionRuntime("Wrong expected status: %d != %d"%(status,statusOutput))
	
	def __sendRequest(self, url:str)->str:
		http=ModuloHttp(url,self.__logger,False)
		http.setUserAgent()
		bean=http.doGet(0, False)
		if bean.status!=ModuloHttp.STATUS_OK:
			raise ExceptionHttp(bean.status)
		return bean.responseBody.decode(ModuloStringhe.CODIFICA_UTF8)
