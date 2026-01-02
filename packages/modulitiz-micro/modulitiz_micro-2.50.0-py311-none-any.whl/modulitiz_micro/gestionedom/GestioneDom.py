from bs4 import BeautifulSoup

from modulitiz_nano.ModuloStringhe import ModuloStringhe
from modulitiz_nano.files.ModuloFiles import ModuloFiles


class GestioneDom(object):
	def __init__(self, percorsoNomefile: str | None, htmlString:str):
		if percorsoNomefile is not None:
			self.percorsoNomefile=percorsoNomefile
			htmlString=ModuloFiles.readFileText(percorsoNomefile, True)
		self.htmlString=htmlString
		self.dom=self.__createObj()
	
	@staticmethod
	def innerHTML(tag):
		"""
		dato in input un tag html della classe BeautifulSoup, restituisce il codice html all'interno di questo tag
		"""
		return "".join([str(x) for x in tag.contents])
	
	def selector(self,cssSelector:str):
		"""
		estrae tutti gli elementi che corrispondono al css selector
		"""
		elementi=self.dom.select(cssSelector)
		return elementi
	
	@staticmethod
	def getAttributeValue(tag, nomeAttr:str):
		oldValue=tag.attrs[nomeAttr]
		return oldValue
	@staticmethod
	def setAttributeValue(tag, nomeAttr:str, value):
		tag.attrs[nomeAttr]=value
		return tag
	
	def save(self):
		htmlOut=str(self.dom).encode(ModuloStringhe.CODIFICA_UTF8)
		with ModuloFiles.open(self.percorsoNomefile, "wb") as file:
			file.write(htmlOut)
	
	def __createObj(self)->BeautifulSoup:
		return BeautifulSoup(self.htmlString, features="html.parser")
