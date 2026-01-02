import smtplib

from modulitiz_nano.ModuloDate import ModuloDate
from modulitiz_nano.ModuloListe import ModuloListe
from modulitiz_nano.ModuloStringhe import ModuloStringhe


class ModuloEmail(object):
	SERVER_GOOGLE_INVIO=('smtp.gmail.com',smtplib.SMTP_SSL_PORT)
	SERVER_VIRGILIO_INVIO=('out.virgilio.it',smtplib.SMTP_SSL_PORT)
	
	def __init__(self,credenzialiServer:tuple,user:str|None,password:str|None,isDebug:bool=False):
		self.credenzialiServer=credenzialiServer
		self.isDebug=isDebug
		self.connEmail=None
		self.user=user
		self.password=password
		self.isLogged=False
	
	def login(self,user:str|None=None,password:str|None=None):
		if self.isLogged:
			return
		# controllo se usare le credenziali dei parametri o quelle della classe
		if user is not None:
			self.user=user
		if password is not None:
			self.password=password
		# mi collego
		self.connEmail=smtplib.SMTP_SSL(*self.credenzialiServer)
		if self.isDebug:
			self.connEmail.set_debuglevel(1)
		# se serve setto l'autenticazione
		if self.user is not None and self.password is not None:
			self.connEmail.login(self.user,self.password)
		self.isLogged=True
	
	def sendWithLoginAndClose(self,destinatari:str|list|tuple, oggetto:str, messaggio:str,
			isHtml:bool)->dict:
		# check if already logged
		if not self.isLogged:
			self.login(self.user,self.password)
		# invio email
		try:
			errors=self.send(None,destinatari,oggetto,messaggio,isHtml)
		except Exception as ex:
			self.close()
			raise ex
		# chiudo la connessione
		self.close()
		return errors
	
	def send(self, mittente:str|None,destinatari:str|list|tuple, oggetto:str, messaggio:str,
			isHtml:bool, dataInvio=ModuloDate.now(), cc=None, ccn=None)->dict:
		# controllo i parametri
		dataInvio=ModuloDate.dateToString(dataInvio)
		if isinstance(destinatari, str):
			destinatari=[destinatari]
		if mittente is None:
			mittente=self.user
		domain=self.user.split("@")[-1]
		messageId=f"{ModuloDate.getSecs()}@{domain}"
		# creo il messaggio
		message=f"""Date: {dataInvio}
From: {mittente}
Subject: {oggetto}
To: {", ".join(destinatari)}
Message-ID: <{messageId}>
"""
		if not ModuloListe.isEmpty(cc):
			message+=("Cc: "+", ".join(cc))+"\n"
		if not ModuloListe.isEmpty(ccn):
			message+=("Bcc: "+", ".join(ccn))+"\n"
		message+="Content-Type: text/html;\n"
		# converto il messaggio in formato html
		if not isHtml:
			messaggio=ModuloStringhe.normalizzaEol(messaggio).replace("\n","<br/>\n")
		messaggio=messaggio.encode(ModuloStringhe.CODIFICA_ASCII,"xmlcharrefreplace").decode(ModuloStringhe.CODIFICA_UTF8)
		message+="\n"+messaggio
		# invio la mail
		try:
			return self.connEmail.sendmail(mittente,destinatari,message)
		except smtplib.SMTPServerDisconnected as ex:
			return {"":str(ex)}
	
	def close(self):
		if self.connEmail is None:
			return
		self.connEmail.quit()
		self.connEmail=None
		self.isLogged=False
