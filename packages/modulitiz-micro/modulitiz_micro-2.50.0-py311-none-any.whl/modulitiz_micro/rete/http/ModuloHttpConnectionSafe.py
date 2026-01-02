import socket
import time
from urllib.error import URLError

import requests

from modulitiz_micro.exceptions.http.ExceptionHttpGeneric import ExceptionHttpGeneric
from modulitiz_micro.exceptions.http.ExceptionHttpRetriesExceeded import ExceptionHttpRetriesExceeded
from modulitiz_nano.ModuloFunzioni import ModuloFunzioni
from modulitiz_nano.ModuloStringhe import ModuloStringhe
from modulitiz_nano.files.ModuloLogging import ModuloLogging


class ModuloHttpConnectionSafe(object):
	"""
	Utility che serve per gestire eventuali errori di rete e riprova a fare la richiesta in caso di errore
	"""
	
	def __init__(self,logger: ModuloLogging|None,raiseExcOnExceededRetries:bool):
		self.__logger=logger
		self.raiseExcOnExceededRetries=raiseExcOnExceededRetries
		
		self.isLoggerEnabled=self.__logger is not None
		self.contaTentativi=0
		self.nomeFunzChiamanti=[]
		self.msgFunzChiamanti=None
	
	def run(self, retries:int,retriesBeforeNotify: int, funzione, *args,**kwargs):
		"""
		se 'retries' e' = -1 allora continua a provare all'infinito
		se 'retriesBeforeNotify' e' = 0 allora in caso di errore di rete notifica subito
		"""
		ritorno = None
		while self._buildIf(self.contaTentativi,retries):
			try:
				ritorno = funzione(*args,**kwargs)
				self.contaTentativi = -1
			except (ExceptionHttpGeneric,ConnectionError,TimeoutError,URLError,
					requests.exceptions.ConnectionError,socket.gaierror) as ex:
				# controllo il tipo di errore
				ModuloHttpConnectionSafe.__checkCodeExc(ex)
				# gestisco l'assenza di connessione
				self.contaTentativi += 1
				# scrivo un messaggio di avviso
				if retriesBeforeNotify == 0 or self.contaTentativi >= retriesBeforeNotify:
					self.__buildMsgAndNotify()
				ModuloHttpConnectionSafe.__dynamicPauseOrRaiseExc(self.contaTentativi, ex)
		self.contaTentativi=0
		self.nomeFunzChiamanti.clear()
		return ritorno
	
	@staticmethod
	def _buildIf(contaTentativi:int,retries:int)->bool:
		return contaTentativi >= 0 and (retries==-1 or contaTentativi<retries)
	
	def __buildMsgAndNotify(self):
		if not self.nomeFunzChiamanti:
			self.msgFunzChiamanti="Errore di connessione nella funzione "+ModuloFunzioni.getFunctionName(1)+"()"
			i=0
			while -1<i<2:
				nomeFunz = ModuloFunzioni.getFunctionName(i+2)
				if not ModuloStringhe.isEmpty(nomeFunz):
					self.msgFunzChiamanti += f", chiamata da {nomeFunz}()"
					i+=1
				else:
					i=-1
		msg=self.msgFunzChiamanti+f"; tentativo numero: {self.contaTentativi}"
		if self.isLoggerEnabled:
			self.__logger.error(msg)
		else:
			print(msg)
		if self.raiseExcOnExceededRetries:
			raise ExceptionHttpRetriesExceeded()
	
	@staticmethod
	def __checkCodeExc(ex: Exception):
		try:
			codiceErrore = ex.code
		except AttributeError:
			codiceErrore = 0
		if codiceErrore in (404, 500):
			raise ex
	
	@staticmethod
	def __dynamicPauseOrRaiseExc(contaTentativi: int, ex: Exception):
		if 0 < contaTentativi <= 20:
			time.sleep(10)
		elif 20 < contaTentativi <= 30:
			time.sleep(60)
		elif 20 < contaTentativi <= 50:
			time.sleep(60 * 2)
		elif 50 < contaTentativi <= 100:
			time.sleep(60 * 5)
		else:
			raise ex
