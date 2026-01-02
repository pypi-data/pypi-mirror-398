from modulitiz_micro.social.telegram.AbstractModuloTelegram import AbstractModuloTelegram


class ModuloTelegramSimple(AbstractModuloTelegram):
	"""
	Utility di gestione semplice per il sistema di messaggistica istantanea Telegram.
	"""
	
	def __init__(self,usernameDestinatario:str|None,*args,**kwargs):
		super().__init__(*args,**kwargs)
		self.usernameDestinatario=usernameDestinatario
	
	@staticmethod
	def getVerificationCodefromUser()->str:
		"""
		Specifica in che modo chiedere all'utente il codice di verifica,
		viene chiesto solo la prima volta che ci si collega.
		"""
		return input('Inserisci il codice di verifica: ')
	
	def sendMessageDefaultDestinatario(self,msg:str):
		"""
		Invia il messaggio al destinatario di default specificato nella creazione di quest'oggetto.
		:param msg: il testo del messaggio da inviare
		"""
		super().sendMessageWithConnectAndClose(self.usernameDestinatario,msg)
