import asyncio
import os.path

from androidtvremote2 import AndroidTVRemote
from androidtvremote2 import CannotConnect
from androidtvremote2 import ConnectionClosed
from androidtvremote2 import InvalidAuth

from modulitiz_micro.rete.ModuloNetworking import ModuloNetworking
from modulitiz_nano.exceptions.ExceptionRuntime import ExceptionRuntime
from modulitiz_nano.files.ModuloLogging import ModuloLogging
from modulitiz_nano.util.decorators.noAwait import noAwait


class ModuleAndroidTVRemote(object):
	API_PORT=6466
	PAIR_PORT=6467
	
	def __init__(self,logger:ModuloLogging,clientName:str,outputDir:str,ip:str):
		self.__logger=logger
		self.__clientName=clientName
		self.__outputDir=outputDir
		self.__ip=ip
		
		self.conn:AndroidTVRemote|None=None
	
	@noAwait
	async def populate(self):
		# check availability
		if not ModuloNetworking.checkPing(self.__ip):
			raise ExceptionRuntime(f"Ip {self.__ip} not found")
		self.__isPortOpen(self.API_PORT)
		self.__isPortOpen(self.API_PORT)
		# create connection
		certFile=os.path.join(self.__outputDir,"cert.pem")
		keyFile=os.path.join(self.__outputDir,"key.pem")
		self.conn=AndroidTVRemote(self.__clientName,certFile,keyFile,self.__ip)
		# pairing
		self.__logger.debug("Start pairing")
		if await self.conn.async_generate_cert_if_missing():
			self.__logger.debug("Generated new certificate")
			await self.__pair()
		while True:
			try:
				await self.conn.async_connect()
				break
			except InvalidAuth:
				self.__logger.exception("Need to pair again")
				await self.__pair()
			except (CannotConnect,ConnectionClosed):
				self.__logger.exception("Cannot connect, exiting")
				return
		await asyncio.sleep(0.2)
		self.__logger.debug("Pair ok")
	
	async def __pair(self):
		name,mac=await self.conn.async_get_name_and_mac()
		self.__logger.info(f"Start Pairing with {self.conn.host} {name} {mac}, this will turn on the Android TV")
		await self.conn.async_start_pairing()
		while True:
			pairing_code=await asyncio.to_thread(input,"Enter pairing code: ")
			try:
				return await self.conn.async_finish_pairing(pairing_code)
			except InvalidAuth:
				self.__logger.exception("Invalid pairing code")
				continue
			except ConnectionClosed:
				self.__logger.exception("Initialize pair again")
				await self.__pair()
	
	def getVolumeLevel(self)->int:
		return self.conn.volume_info["level"]
	
	@noAwait
	async def setVolumeLevel(self,level: int):
		currentLevel=self.getVolumeLevel()
		diff=currentLevel-level
		if diff==0:
			return
		cmd="VOLUME_DOWN" if diff>0 else "VOLUME_UP"
		# pause needed for elaborating data
		await asyncio.sleep(0.4)
		for _ in range(abs(diff)):
			self.conn.send_key_command(cmd)
		await asyncio.sleep(0.4)
		# check if level is correct
		currentLevel=self.getVolumeLevel()
		if level!=currentLevel:
			raise ExceptionRuntime(f"Current volume level {currentLevel} don't equals {level}")
	
	@noAwait
	async def sendCommand(self,cmd:str):
		# pause needed for elaborating data
		await asyncio.sleep(0.4)
		self.conn.send_key_command(cmd)
		await asyncio.sleep(0.4)
	
	def isOn(self)->bool:
		if self.conn is None:
			return False
		return self.conn.is_on
	
	def close(self):
		if self.conn is None:
			return
		self.conn.disconnect()
		self.conn = None
	
	def __isPortOpen(self,port:int):
		if ModuloNetworking.isHttpPortOpen(self.__ip,port):
			return
		raise ExceptionRuntime(f"Port {port} on ip {self.__ip} not open")
