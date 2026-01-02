import gzip
import json
import logging
import ssl
import urllib
from urllib.parse import urlencode
from urllib.request import Request

import brotli

from modulitiz_micro.rete.http.ModuloHttpConnectionSafe import ModuloHttpConnectionSafe
from modulitiz_micro.rete.http.beans.HttpResponseBean import HttpResponseBean
from modulitiz_micro.rete.http.decorators.catchAndRaiseHttpExceptions import catchAndRaiseHttpExceptions
from modulitiz_nano.ModuloBase64 import ModuloBase64
from modulitiz_nano.ModuloStringhe import ModuloStringhe
from modulitiz_nano.exceptions.ExceptionRuntime import ExceptionRuntime
from modulitiz_nano.files.ModuloLogging import ModuloLogging


class ModuloHttp(object):
	"""
	Utility per gestione richieste di rete secondo il protocollo HTTP.
	"""
	
	UA_ANDROID="Mozilla/5.0 (Linux; Android 12.0; SM-G900P Build/LRX21T) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Mobile Safari/537.36"
	
	UA_MACOS_CHROME="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"
	UA_WINDOWS_CHROME="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"
	UA_WINDOWS_FIREFOX="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:144.0) Gecko/20100101 Firefox/144.0"
	
	UAS=[UA_MACOS_CHROME,UA_WINDOWS_CHROME,UA_WINDOWS_FIREFOX]
	
	URL_CERCA_GOOGLE="https://www.google.it/search?q="
	# https://ipecho.net/plain removed because it can return either ipv4 or ipv6 depending on your ISP/Internet connection
	URLS_GET_IPV4=('https://ipinfo.io/ip','https://api.ipify.org','https://ipv4.seeip.org')
	
	REGEX_IPV4_ADDRESS=r"\b(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.){3}(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\b"
	
	STATUS_OK=200
	STATUS_OK_PARTIAL_CONTENT=206
	
	
	def __init__(self,url:str,logger:ModuloLogging|None,useProxy:bool):
		logging.getLogger("urllib3").propagate=False
		
		self.__requestObj=Request(url)
		self.__logger=logger
		
		self.setUserAgent(self.UA_WINDOWS_FIREFOX)
		self.addHeader('Accept-Encoding','gzip, deflate, br')		# questo serve per ridurre la dimensione della risposta
		if useProxy:
			self.addHeader('Origin','localhost')
		self.connectionSafe=ModuloHttpConnectionSafe(self.__logger,False)
	
	def doGet(self,retries:int,ignoreCerts:bool=False)->HttpResponseBean:
		"""
		Esegue una richiesta di tipo GET
		"""
		if retries==0:
			return self.__getOrPost(ignoreCerts)
		return self.connectionSafe.run(retries,0,self.__getOrPost,ignoreCerts)
	
	def doPost(self, postData:dict, asJson:bool, retries:int,ignoreCerts:bool=False)->HttpResponseBean:
		"""
		Esegue una richiesta di tipo POST
		"""
		if not asJson:
			postDataEncoded=urlencode(postData)
		else:
			postDataEncoded=json.dumps(postData)
			self.addHeader("Content-Type","application/json; charset=utf-8")
		postDataEncoded=postDataEncoded.encode()
		self.__requestObj.data=postDataEncoded
		if retries==0:
			return self.__getOrPost(ignoreCerts)
		return self.connectionSafe.run(retries,0,self.__getOrPost,ignoreCerts)
	
	@catchAndRaiseHttpExceptions
	def __getOrPost(self, ignoreCerts:bool)->HttpResponseBean:
		# ignoro certificati
		ctx=None
		if ignoreCerts:
			ctx=ssl.create_default_context()
			ctx.check_hostname=False
			ctx.verify_mode=ssl.CERT_NONE
		# send request
		with urllib.request.urlopen(self.__requestObj,context=ctx) as response:
			responseBody=response.read()
			responseHeaders=response.info()
			status=response.status
		# se il server manda il contenuto in formato compresso lo decomprimo
		contentEncoding=responseHeaders.get('Content-Encoding')
		if contentEncoding=="gzip":
			responseBody=gzip.decompress(responseBody)
		elif contentEncoding=="br":
			responseBody=brotli.decompress(responseBody)
		elif contentEncoding is not None and contentEncoding!= "deflate":
			raise ExceptionRuntime("Codifica '"+contentEncoding+"' non gestita.")
		return HttpResponseBean(status,responseBody,responseHeaders)
	
	# opzioni aggiuntive
	def addHeader(self,nome:str,valore):
		if ModuloStringhe.isEmpty(valore):
			return
		self.__requestObj.add_header(nome,valore)
	
	def setUserAgent(self,userAgent:str=None):
		if ModuloStringhe.isEmpty(userAgent):
			userAgent=self.UA_ANDROID
		else:
			userAgent=userAgent.strip()
		self.addHeader('User-Agent',userAgent)
	
	def setDownloadRange(self,inizio:int,fine:int):
		self.addHeader('Range',"bytes="+str(inizio)+"-"+str(fine))
	
	def setAuthenticationBasic(self,username:str,password:str):
		authStr=ModuloBase64.codificaStr('%s:%s' % (username, password))
		self.addHeader('Authorization',"Basic "+authStr)
