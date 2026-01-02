from OpenSSL import crypto

from modulitiz_nano.ModuloDate import ModuloDate
from modulitiz_nano.ModuloStringhe import ModuloStringhe


class ModuloSsl(object):
	CA_CERT_FILE="cert.pem"
	
	def __init__(self):
		self.cert: crypto.X509|None=None
		self.certStr: str|None=None
	
	def createSelfSignedCertAnonymous(self):
		return self.createSelfSignedCert("XX","XX","Xxx","Xxx","Xx","Xx","x@x.com")
	
	def createSelfSignedCert(self,stato: str,provincia: str,via: str,organizzazione: str,organizzazioneUnita: str,nomeComune: str,email: str):
		privateKey=crypto.PKey()
		privateKey.generate_key(crypto.TYPE_RSA,2048)
		
		certReq=crypto.X509Req()
		certReq.get_subject().C=stato
		certReq.get_subject().ST=provincia
		certReq.get_subject().L=via
		certReq.get_subject().O=organizzazione
		certReq.get_subject().OU=organizzazioneUnita
		certReq.get_subject().CN=nomeComune
		certReq.get_subject().emailAddress=email
		certReq.set_pubkey(privateKey)
		certReq.sign(privateKey,'sha256')
		
		certIssuer=crypto.X509Req()
		certIssuer.get_subject().C=stato
		certIssuer.get_subject().ST=provincia
		certIssuer.get_subject().L=via
		certIssuer.get_subject().O=organizzazione
		certIssuer.get_subject().OU=organizzazioneUnita
		certIssuer.get_subject().CN=nomeComune
		certIssuer.get_subject().emailAddress=email
		certIssuer.set_pubkey(privateKey)
		certIssuer.sign(privateKey,'sha256')
		
		cert=crypto.X509()
		cert.set_serial_number(ModuloDate.getSecs())
		cert.gmtime_adj_notBefore(0)
		cert.gmtime_adj_notAfter(5*365*24*60*60)
		cert.set_issuer(certIssuer.get_subject())
		cert.set_subject(certReq.get_subject())
		cert.set_pubkey(certReq.get_pubkey())
		cert.sign(privateKey,'sha256')
		self.cert=cert
		
		certStr=crypto.dump_certificate(crypto.FILETYPE_PEM,cert).decode(ModuloStringhe.CODIFICA_UTF8)
		certStr+=certStr
		certStr+=crypto.dump_privatekey(crypto.FILETYPE_PEM,privateKey).decode(ModuloStringhe.CODIFICA_UTF8)
		self.certStr=certStr
