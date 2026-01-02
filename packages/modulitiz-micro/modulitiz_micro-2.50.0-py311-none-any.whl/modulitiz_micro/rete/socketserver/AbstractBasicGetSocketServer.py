from abc import abstractmethod

from modulitiz_micro.exceptions.http.ExceptionHttp import ExceptionHttp
from modulitiz_micro.rete.http.ModuloHttp import ModuloHttp
from modulitiz_micro.rete.socketserver.AbstractSocketServer import AbstractSocketServer
from modulitiz_nano.ModuloStringhe import ModuloStringhe


class AbstractBasicGetSocketServer(AbstractSocketServer):
	
	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)
	
	@abstractmethod
	def processResponse(self,clientIp:str,path:str,params:dict)->str|None:
		"""
		Cosa fare se la richiesta e' formalmente corretta.
		Deve ritornare un output per chi ha fatto la richiesta
		"""
	
	def handleRequest(self,method:str,url:str,path:str,params:dict,httpType:str,clientIp:str,_clientPort:int)->tuple:
		if method!='GET' or not ModuloStringhe.contains(httpType,'HTTP') or ModuloStringhe.isEmpty(url):
			return 500,None,None
		# controllo parametri
		httpCode=ModuloHttp.STATUS_OK
		responseBody=""
		try:
			responseBody=self.processResponse(clientIp,path,params)
		except Exception as ex:
			if not isinstance(ex, ExceptionHttp):
				self.callbackError(ex)
				httpCode=500
			else:
				httpCode=ex.httpCode
		return httpCode,None,responseBody
