from modulitiz_micro.rete.ntp.AbstractModuloNtp import AbstractModuloNtp


class ModuloNtpIt(AbstractModuloNtp):
	HOST_IT="ntp1.inrim.it"
	
	def __init__(self,*args,**kwargs):
		super().__init__(self.HOST_IT,*args,**kwargs)
