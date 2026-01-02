class EmailBean(object):
	def __init__(self,diz:dict):
		self.destinatario:str=diz['destinatario']
		self.user:str=diz['user']
		self.password:str=diz['password']
