import socket
import struct
from abc import ABC

from modulitiz_micro.exceptions.http.ExceptionHttpGeneric import ExceptionHttpGeneric
from modulitiz_micro.rete.http.ModuloHttpConnectionSafe import ModuloHttpConnectionSafe
from modulitiz_micro.rete.http.decorators.catchAndRaiseHttpExceptions import catchAndRaiseHttpExceptions
from modulitiz_nano.ModuloDate import ModuloDate
from modulitiz_nano.files.ModuloLogging import ModuloLogging


class AbstractModuloNtp(ABC):
	REFRESH_CACHE_EVERY_SECS=4*3600*1000		# NTP request frequency
	OFFSET_MILLIS=1		# offset correzione errore
	TIMEOUT=10
	
	__PORTA=123						# numero della porta (UDP)
	__BUF=1024
	__TIME1970=2208988800			# reference time, secondi da 1900-01-01 00:00:00 a 1970-01-01 00:00:00 = 70 anni
	__MSG=('\x1b' + 47 * '\0').encode()
	
	
	def __init__(self,host:str,logger:ModuloLogging):
		self.logger=logger
		self.connectionSafe = ModuloHttpConnectionSafe(logger,False)
		self.host=host
		self.lastNtpResponse=0
		self.lastNtpTimestampUtc=0
	
	def getTimestampUtcFromNtp(self,useCache:bool=True,retryIfError:bool=True)->int:
		if useCache is True and self.lastNtpResponse!=0:
			# controllo se e' passato poco tempo dall'ultima chiamata ntp
			diffMillisLastResponse=(ModuloDate.getMillis()-self.lastNtpResponse)
			if diffMillisLastResponse<self.REFRESH_CACHE_EVERY_SECS:
				# calcolo l'ora attuale usando il cronometro interno
				return self.lastNtpTimestampUtc+diffMillisLastResponse+self.OFFSET_MILLIS
		# invio la richiesta e in caso di errore...
		if not retryIfError:
			#... uso il cronometro interno
			try:
				timestampUtc=self.__ntpSendPacket()
			except ExceptionHttpGeneric:
				timestampUtc=None
		else:
			#... riprovo
			timestampUtc=self.connectionSafe.run(1,3,self.__ntpSendPacket)
		if timestampUtc is None:
			diffMillisLastResponse=(ModuloDate.getMillis()-self.lastNtpResponse)
			return self.lastNtpTimestampUtc+diffMillisLastResponse+self.OFFSET_MILLIS
		timestampUtc=timestampUtc*1000
		# successo
		self.lastNtpResponse=ModuloDate.getMillis()
		self.lastNtpTimestampUtc=timestampUtc
		return self.lastNtpTimestampUtc
	
	def getDatetimeFromNtp(self,useCache:bool=True,retryIfError:bool=True):
		tsSec=self.getTimestampUtcFromNtp(useCache,retryIfError)//1000
		return ModuloDate.timestampUtcToDate(tsSec)
	
	@catchAndRaiseHttpExceptions
	def __ntpSendPacket(self)->int:
		# connect to server
		client=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		client.settimeout(self.TIMEOUT)
		client.sendto(self.__MSG,(self.host,self.__PORTA))
		# ricevo i dati
		response=client.recvfrom(self.__BUF)[0]
		# chiudo la socket
		client.close()
		# estraggo il timestamp
		tsSec=struct.unpack("!12I",response)[10]
		tsSec-=self.__TIME1970
		return tsSec
