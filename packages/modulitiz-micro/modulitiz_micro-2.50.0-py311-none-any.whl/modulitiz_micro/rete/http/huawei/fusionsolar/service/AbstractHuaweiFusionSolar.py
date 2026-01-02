import json
from abc import ABC

from modulitiz_micro.rete.http.ModuloHttp import ModuloHttp
from modulitiz_micro.rete.http.beans.HttpResponseBean import HttpResponseBean
from modulitiz_micro.rete.http.huawei.fusionsolar.beans.TokenBean import TokenBean
from modulitiz_micro.rete.http.huawei.fusionsolar.exceptions.ExceptionTooManyLogins import ExceptionTooManyLogins
from modulitiz_nano.ModuloStringhe import ModuloStringhe
from modulitiz_nano.exceptions.ExceptionRuntime import ExceptionRuntime
from modulitiz_nano.files.ModuloFiles import ModuloFiles
from modulitiz_nano.files.ModuloLogging import ModuloLogging


class AbstractHuaweiFusionSolar(ABC):
	URL_PREFIX="https://eu5.fusionsolar.huawei.com/thirdData/"
	XSRF_TOKEN="XSRF-TOKEN"
	
	def __init__(self,logger:ModuloLogging, user: str,pwd: str,sessionFileName: str, retries:int):
		self._logger=logger
		self.__user=user
		self.__pwd=pwd
		self.__sessionFileName=sessionFileName
		self.__retries=retries
		self.countRequests=0
		self.__tokenBean:TokenBean|None=None
	
	def populate(self):
		if ModuloFiles.getFileSize(self.__sessionFileName)<=0:
			return
		# load token
		with open(self.__sessionFileName,"rt") as f:
			diz=json.load(f)
			self.__tokenBean=TokenBean.fromDict(diz)
	
	def __login(self):
		self._makeGenericRequest("login", {"userName":self.__user,"systemCode":self.__pwd})
	
	def _makeGenericRequest(self,urlSuffix: str, postData:dict)->dict:
		isLogin=urlSuffix=="login"
		if not isLogin:
			# check if login is needed
			if self.__tokenBean is None or self.__tokenBean.isExpired():
				self.__login()
		else:
			# check if it's too early to call login
			if self.__tokenBean is not None and self.__tokenBean.isTooEarly():
				raise ExceptionTooManyLogins()
		bean=self._makeInnerRequest(urlSuffix, postData, isLogin)
		if bean.status!=ModuloHttp.STATUS_OK:
			raise ExceptionRuntime("Status code %d"%(bean.status,))
		# parse content
		responseText=bean.responseBody.decode(ModuloStringhe.CODIFICA_UTF8)
		if ModuloStringhe.isEmpty(responseText):
			raise ExceptionRuntime("Response empty")
		jsonObj=json.loads(responseText)
		failCode=jsonObj['failCode']
		if not jsonObj['success'] or failCode!=0:
			raise ExceptionRuntime("Response call '%s' error %d:\n%s"%(urlSuffix,failCode,responseText))
		# save token
		if isLogin:
			self.__tokenBean=TokenBean(bean.responseHeaders[self.XSRF_TOKEN])
			with open(self.__sessionFileName,"wt") as f:
				json.dump(self.__tokenBean.toDict(),f,indent=4)
		return jsonObj['data']
	
	def _makeInnerRequest(self,urlSuffix: str,postData: dict, isLogin:bool) -> HttpResponseBean:
		moduleHttp=ModuloHttp(self.URL_PREFIX+urlSuffix,self._logger,False)
		if not isLogin:
			moduleHttp.addHeader(self.XSRF_TOKEN,self.__tokenBean.value)
		bean=moduleHttp.doPost(postData,True,self.__retries,False)
		self.countRequests+=1
		return bean
