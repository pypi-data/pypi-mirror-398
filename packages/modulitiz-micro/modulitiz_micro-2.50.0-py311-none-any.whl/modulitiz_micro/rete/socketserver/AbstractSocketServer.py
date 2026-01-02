import errno
import os
import socket
import ssl
import time
from _io import BufferedReader
from abc import ABC
from abc import abstractmethod

from modulitiz_micro.rete.ModuloNetworking import ModuloNetworking
from modulitiz_micro.rete.http.ModuloHttp import ModuloHttp
from modulitiz_micro.rete.http.ModuloHttpUtils import ModuloHttpUtils
from modulitiz_micro.rete.ssl.ModuloSsl import ModuloSsl
from modulitiz_nano.ModuloListe import ModuloListe
from modulitiz_nano.ModuloStringhe import ModuloStringhe
from modulitiz_nano.exceptions.ExceptionRuntime import ExceptionRuntime
from modulitiz_nano.files.ModuloFiles import ModuloFiles
from modulitiz_nano.files.ModuloLogging import ModuloLogging
from modulitiz_nano.multithread.ModuloThread import ModuloThread


class AbstractSocketServer(ABC):
	HTTP_CODES={
		ModuloHttp.STATUS_OK:"OK",
		404:"Not Found",
		500:"Internal Server Error",
		501:"Not Implemented",
	}
	
	MAX_CONNECTIONS=10
	TIMEOUT_SERVER=30
	TIMEOUT_CLIENT=60
	
	TIPO_RESPONSE__PLAIN_TEXT=1
	TIPO_RESPONSE__STREAM=2
	
	def __init__(self,logger:ModuloLogging,porta:int,percorsoFileCertSsl:str):
		self._logger=logger
		self.__porta=porta
		self.__percorsoFileCertSsl=percorsoFileCertSsl
		
		self.isRequestedExit=False
		self.countActiveConnections=0
		self.contextSsl=None
		self.serverSocket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	
	def populate(self):
		# controllo che la porta non sia gia' occupata
		if self.isOpen():
			raise ExceptionRuntime(f"La porta {self.__porta} e' gia' aperta")
		# ssl
		if self.__percorsoFileCertSsl is not None:
			# se il certificato non esiste lo creo
			if ModuloFiles.getFileSize(self.__percorsoFileCertSsl)==-1:
				self._logger.info("Generazione certificato...")
				moduloSsl=ModuloSsl()
				moduloSsl.createSelfSignedCertAnonymous()
				with ModuloFiles.open(self.__percorsoFileCertSsl,"w+t") as fp:
					fp.write(moduloSsl.certStr)
			contextSsl=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
			contextSsl.load_cert_chain(certfile=self.__percorsoFileCertSsl)
			self.contextSsl=contextSsl
		# creo la socket
		self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.serverSocket.bind(('0.0.0.0', self.__porta))
		self.serverSocket.listen(self.MAX_CONNECTIONS)
		self.serverSocket.settimeout(self.TIMEOUT_SERVER)
	
	@abstractmethod
	def callbackError(self,ex: Exception):
		"""
		Cosa fare in caso di errore della socket
		"""
	
	@abstractmethod
	def handleRequest(self,method:str,url:str,path:str,params:dict,httpType:str,clientIp:str,clientPort:int)->tuple:
		"""
		Cosa fare se un client contatta il server.
		Deve ritornare una tupla: (httpCode,header,body)
		"""
	
	def isOpen(self)->bool:
		return ModuloNetworking.isHttpPortOpen(None, self.__porta)
	
	def avvia(self):
		protocolSuffix="S" if self.contextSsl is not None else ""
		self._logger.info("Server in ascolto sulla porta HTTP%s %d",protocolSuffix,self.__porta)
		ModuloThread.startDaemonWithCallbackError(self.callbackError,self.__avviaLoopNoThreaded,())
	
	def chiudi(self):
		if not self.isOpen():
			return
		self.isRequestedExit=True
		while self.countActiveConnections>0:
			time.sleep(0.5)
		# qui socket.shutdown() non ci vuole perche' deve essere usato solo lato client
		self.serverSocket.close()
	
	def __avviaLoopNoThreaded(self):
		while not self.isRequestedExit:
			self.__avviaNoThreaded()
		self.countActiveConnections=0
	def __avviaNoThreaded(self):
		# aspetto una richiesta
		try:
			clientConnection,(clientIp,clientPort)=self.serverSocket.accept()
		except TimeoutError:
			clientConnection=None
			clientIp=None
			clientPort=None
		except OSError as osError:
			if osError.errno not in(errno.ENOTSOCK,errno.EBADF):
				self.callbackError(osError)
			clientConnection=None
			clientIp=None
			clientPort=None
		if clientConnection is None:
			return
		self.countActiveConnections+=1
		# richiedo i dati
		request=None
		try:
			clientConnection.settimeout(self.TIMEOUT_CLIENT)
			if self.contextSsl is not None:
				clientConnection=self.contextSsl.wrap_socket(clientConnection,server_side=True)
			request=clientConnection.recv(1024)
		except (ssl.SSLEOFError,ssl.SSLZeroReturnError,TimeoutError):
			self.countActiveConnections-=1
		except ssl.SSLError as ex:
			if ex.reason not in(
					"NO_SHARED_CIPHER",
					"TLSV1_ALERT_UNKNOWN_CA",
					"SSLV3_ALERT_BAD_CERTIFICATE","SSLV3_ALERT_CERTIFICATE_UNKNOWN",
					"HTTP_REQUEST","HTTPS_PROXY_REQUEST",
					"UNKNOWN_PROTOCOL","WRONG_VERSION_NUMBER","WRONG_SSL_VERSION"):
				self.callbackError(ex)
			self.countActiveConnections-=1
		except OSError as ex:
			self.__handleOsError(ex)
			self.countActiveConnections-=1
		if request is None:
			clientConnection.close()
			return
		# decodifico la richiesta
		try:
			request=request.decode(ModuloStringhe.CODIFICA_UTF8)
		except UnicodeDecodeError:
			request = None
			self.countActiveConnections -= 1
		if request is None:
			clientConnection.close()
			return
		ModuloThread.startDaemonWithCallbackError(self.callbackError,self.__handleRequestNoThreaded,(request,clientConnection,clientIp,clientPort))
	
	def __handleRequestNoThreaded(self,request:str|None,clientConnection,clientIp:str,clientPort:int):
		valori=self.__parseRequest(request)
		if valori is not None:
			httpCode,responseHeader,responseBody=self.handleRequest(*valori,clientIp,clientPort)
			response,tipo=self.__parseResponse(httpCode,responseHeader,responseBody)
		else:
			responseBody=None
			response,tipo=self.__parseResponse(500,None,None)
		
		if tipo==self.TIPO_RESPONSE__PLAIN_TEXT:
			self.__sendResponse(clientConnection,response)
		elif tipo==self.TIPO_RESPONSE__STREAM and responseBody is not None:
			self.__sendResponse(clientConnection,response)
			# se e' un file pointer leggo e invio un po' alla volta
			fp=responseBody
			chunk=fp.read(1024)
			while chunk:
				clientConnection.send(chunk)
				chunk=fp.read(1024)
			fp.close()
		else:
			response,tipo=self.__parseResponse(500,None,None)
			self.__sendResponse(clientConnection,response)
		try:
			clientConnection.shutdown(socket.SHUT_RDWR)
		except OSError as e:
			if e.errno!=errno.ENOTCONN:
				raise e
		clientConnection.close()
		self.countActiveConnections-=1
	
	@staticmethod
	def __parseRequest(request:str)->tuple|None:
		request=ModuloStringhe.normalizzaEol(request)
		index=request.find('\n\n')
		if index==-1:
			return None
		headers=request[0:index]
		headers=headers.split("\n")
		# la prima riga dell'header deve contenere 3 info
		header=headers[0]
		if ModuloStringhe.isEmpty(header):
			return None
		arr=header.split()
		method=ModuloListe.collectionSafeGet(arr,0)
		url=ModuloListe.collectionSafeGet(arr,1)
		httpType=ModuloListe.collectionSafeGet(arr,2)
		if method is None or url is None or httpType is None:
			return None
		
		url=ModuloHttpUtils.decodeUrl(url)
		if not ModuloStringhe.contains(url,"?"):
			return method,url,url,{},httpType
		# controllo url
		path,params=url.split("?",1)
		path=path[1:]
		params=params.split("&")
		params=[x.split('=') for x in params]
		params=dict(zip([x[0] for x in params],[x[1] if len(x)>=2 else None for x in params]))
		return method,url,path,params,httpType
	
	def __parseResponse(self,httpCode:int,responseHeader:str|None,responseBody)->tuple:
		if responseHeader is None:
			responseHeader=""
		if responseBody is None:
			responseBody=""
		
		lunghezza=None
		tipo=None
		filename=None
		if isinstance(responseBody,str):
			contentType="text/plain; charset=UTF-8"#TODO: se cors usare contentType dell'origine
			tipo=self.TIPO_RESPONSE__PLAIN_TEXT
			responseBody=ModuloStringhe.normalizzaEol(responseBody.rstrip())
			lunghezza=len(responseBody.encode(ModuloStringhe.CODIFICA_UTF8))
		elif isinstance(responseBody,BufferedReader):
			contentType="application/octet-stream"
			tipo=self.TIPO_RESPONSE__STREAM
			filename=os.path.basename(responseBody.name)
		else:
			contentType="text/plain; charset=UTF-8"
			httpCode=501
		
		responseHeader+=("HTTP/1.1 %d %s"%(httpCode,self.HTTP_CODES.get(httpCode,"")))
		if httpCode==ModuloHttp.STATUS_OK:
			if lunghezza is not None:
				responseHeader+="\nContent-Length: "+str(lunghezza)
			if filename is not None:
				responseHeader+='\nContent-Disposition: attachment; filename="'+filename+'"'
		responseHeader+=f"""
Access-Control-Allow-Origin: *
Content-Type: {contentType}
Connection: close
X-Robots-Tag: noindex, nofollow"""
		#compongo response
		response=responseHeader+"\n\n"
		if tipo==self.TIPO_RESPONSE__PLAIN_TEXT:
			response+=responseBody
		response=ModuloStringhe.normalizzaEol(response)
		response=response.encode(ModuloStringhe.CODIFICA_UTF8)
		return response,tipo
	
	@staticmethod
	def __sendResponse(clientConnection,response):
		try:
			clientConnection.sendall(response)
		except (ConnectionResetError,BrokenPipeError,ssl.SSLEOFError,ssl.SSLZeroReturnError):
			pass
	
	def __handleOsError(self,ex:OSError):
		if ex.errno in (errno.ECONNRESET,errno.ETIMEDOUT):
			return
		self.callbackError(ex)
