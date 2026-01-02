import oracledb

from modulitiz_micro.database.ModuloSqlServer import ModuloSqlServer


class ModuloSqlOracle(ModuloSqlServer):
	DEFAULT_PORTA=1521
	
	def __init__(self,porta:int|None,*args,**kwargs):
		super().__init__(*args,**kwargs)
		if porta is None:
			porta=self.DEFAULT_PORTA
		self.porta=porta
	
	def connessione(self):
		dsn="{}/{}@{}:{}/xe".format(self.username,self.password,self.host,self.porta)
		self.connDb=oracledb.connect(dsn)
		self.connDb=dsn
	
