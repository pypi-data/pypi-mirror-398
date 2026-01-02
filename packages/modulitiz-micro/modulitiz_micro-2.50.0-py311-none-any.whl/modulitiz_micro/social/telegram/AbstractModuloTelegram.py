from abc import ABC
from abc import abstractmethod

from telethon import TelegramClient

from modulitiz_nano.ModuloStringhe import ModuloStringhe
from modulitiz_nano.util.decorators.noAwait import noAwait


class AbstractModuloTelegram(ABC):
	def __init__(self,apiId:int,apiHash:str,nomefileSessione:str,phoneNumWithCountryCode:str):
		self.apiId=apiId
		self.apiHash=apiHash
		self.nomefileSessione=nomefileSessione
		self.phoneNumWithCountryCode=phoneNumWithCountryCode
		
		self.client:TelegramClient|None = None
	
	@noAwait
	async def connect(self):
		self.client = TelegramClient(self.nomefileSessione, self.apiId, self.apiHash)
		await self.client.connect()
		# se il client non e' autorizzato richiedo la verifica
		if await self.client.is_user_authorized():
			return
		await self.client.send_code_request(self.phoneNumWithCountryCode)
		await self.client.sign_in(self.phoneNumWithCountryCode, self.getVerificationCodefromUser())
	
	def sendMessageWithConnectAndClose(self,username: str|None,msg: str):
		"""
		Apre la connessione, invia il messaggio e chiude la connessione.
		:param username: il nome utente del destinatario a cui mandare il messaggio
		:param msg: il testo del messaggio da inviare
		"""
		if ModuloStringhe.isEmpty(username):
			return
		self.connect()
		self.sendMessage(username,msg)
		self.close()
	
	@noAwait
	async def sendMessage(self,username:str,msg:str):
		await self.client.send_message(username, msg, parse_mode='html')
	
	def close(self):
		self.client.disconnect()
	
	@staticmethod
	@abstractmethod
	def getVerificationCodefromUser()->str:
		"""
		Deve ritornare una stringa che corrisponde al codice di verifica inserito dall'utente.
		"""
