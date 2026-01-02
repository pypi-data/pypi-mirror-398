from modulitiz_micro.iot.enums.IotOSEnum import IotOSEnum


class IotDeviceBean(object):
	"""
	Classe che definisce la struttura di una voce complessa del file di configurazione del programma.
	Elenca le proprietà che identificano un dispositivo/sensore Internet Of Things.
	"""
	
	def __init__(self,ip:str, os:IotOSEnum, key:str):
		self.ip=ip
		self.os=os
		self.key=key
