from modulitiz_micro.rete.ntp.ModuloNtpIt import ModuloNtpIt

from modulitiz_nano.util.beans.globalvar.AbstractGlobalVarBean import AbstractGlobalVarBean


class AbstractBasicGlobalVarBean(AbstractGlobalVarBean):
	"""
	Classe da usare come base per definire la struttura di una classe che raggrupperà gli oggetti che verranno usati nel programma
	"""
	
	def __init__(self,useNtp:bool,*args,**kwargs):
		super().__init__(*args,**kwargs)
		if useNtp:
			self.moduloNtp=ModuloNtpIt(self.logger)
	
