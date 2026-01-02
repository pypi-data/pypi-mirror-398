import os

from modulitiz_nano.sistema.ModuloSystem import ModuloSystem


class ModuloEnvVars(object):
	
	@classmethod
	def add(cls,nomeVar:str,valore:str,addFirst:bool):
		if not ModuloSystem.isWindows():
			separatore=":"
		else:
			separatore=";"
		nomeVar=nomeVar.upper()
		if not cls.exist(nomeVar):
			cls.setOrReplace(nomeVar,valore)
			return
		if addFirst:
			cls.setOrReplace(nomeVar,valore+separatore+os.environ[nomeVar])
		else:
			if not os.environ[nomeVar].endswith(separatore):
				os.environ[nomeVar]+=separatore
			os.environ[nomeVar]+=valore
	@staticmethod
	def setOrReplace(nomeVar:str,valore:str):
		os.environ[nomeVar]=valore

	@staticmethod
	def getOrNone(nomeVar:str)->str|None:
		return os.environ.get(nomeVar,None)
	
	@staticmethod
	def exist(nomeVar:str)->bool:
		return nomeVar in os.environ
