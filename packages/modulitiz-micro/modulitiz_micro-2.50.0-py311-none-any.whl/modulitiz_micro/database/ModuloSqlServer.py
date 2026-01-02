import pypyodbc

from modulitiz_micro.database.AbstractSql import AbstractSql


class ModuloSqlServer(AbstractSql):
	ERROR_CODE__UNIQUE_INDEX=23000
	
	def __init__(self,host:str,nome_db:str,username:str,password:str):
		super().__init__()
		self.host=host
		self.nome_db=nome_db
		self.username=username
		self.password=password
		
	def connessione(self):
		connDb=pypyodbc.connect("Driver={SQL Server};Server="+self.host+";Database="+self.nome_db+";uid="+self.username+";pwd="+self.password+";")
		self.connDb=connDb
	
	def select(self,sql:str,params:list):
		with self.initCursor() as cursoreDb:
			cursoreDb.execute(sql,params)
			results=list(cursoreDb)
		return results
	
	def select_count(self,cursoreDb,sql:str,params:list)->int:
		with cursoreDb:
			cursoreDb.execute(sql,params)
			output=self.count(cursoreDb)
		return output
	
	def modifica(self,cursoreDb,sql:str,params:list,ignore_unique_index:bool):
		"""
		Use it for data modifications like: insert, update, delete
		"""
		try:
			cursoreDb.execute(sql,params)
		except pypyodbc.IntegrityError as ie:
			if ignore_unique_index:
				error_code=int(ie.value[0])
				if error_code!=self.ERROR_CODE__UNIQUE_INDEX:
					raise ie
	
