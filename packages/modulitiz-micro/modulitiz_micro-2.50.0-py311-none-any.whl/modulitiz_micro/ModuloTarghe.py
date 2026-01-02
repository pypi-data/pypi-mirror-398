from modulitiz_nano.ModuloNumeri import ModuloNumeri
from modulitiz_nano.ModuloStringhe import ModuloStringhe
from modulitiz_micro.gestionedom.GestioneDom import GestioneDom
from modulitiz_micro.rete.http.ModuloHttp import ModuloHttp


class ModuloTarghe(object):
	"""
	Utility di gestione delle targhe delle auto.
	"""
	
	URL="https://autokar.it/targhe"
	
	@classmethod
	def getAnno(cls,targa:str)->int|None:
		"""
		Cerca la targa e restituisce approssimativamente l'anno di immatricolazione.
		:param targa: la targa dell'auto da cercare.
		"""
		http=ModuloHttp(cls.URL,None,False)
		responseBody=http.doGet(3,True).responseBody.decode(ModuloStringhe.CODIFICA_LATIN1)
		gestioneDom=GestioneDom(None,responseBody)
		elementi=gestioneDom.selector(".entry-content p")
		targaIniziale=targa[:2]
		for elem in elementi:
			anno=cls.__getAnno(elem,targaIniziale)
			if anno is not None:
				return anno
		return None
	
	@classmethod
	def __getAnno(cls,tag,targaIniziale:str)->int|None:
		elementi=tag.contents
		if len(elementi)!=2:
			return None
		try:
			testo=elementi[0].contents[0]
		except AttributeError:
			return None
		if targaIniziale!=testo:
			return None
		annoStr=elementi[1].strip()
		anno=ModuloNumeri.strToInt(annoStr)
		if anno is not None:
			return anno
		anno=int(annoStr.split(" ")[0])
		return anno
