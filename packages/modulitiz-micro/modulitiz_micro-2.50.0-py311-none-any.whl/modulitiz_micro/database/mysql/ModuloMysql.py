from abc import abstractmethod

import mysql.connector

from modulitiz_micro.database.AbstractSql import AbstractSql
from modulitiz_micro.database.exceptions.ExceptionDbNoData import ExceptionDbNoData
from modulitiz_micro.database.mysql.MysqlCommonConverter import MysqlCommonConverter
from modulitiz_nano.ModuloListe import ModuloListe
from modulitiz_nano.ModuloStringhe import ModuloStringhe
from modulitiz_nano.exceptions.ExceptionRuntime import ExceptionRuntime
from modulitiz_nano.files.ModuloFiles import ModuloFiles
from modulitiz_nano.files.ModuloLogging import ModuloLogging
from modulitiz_nano.sistema.ModuloSystem import ModuloSystem


class ModuloMysql(AbstractSql):
	"""
	select
	count
	insert
	update
	delete
	"""
	
	DATE_TIME_NOW="NOW()"
	
	DEFAULT_PORT=3306
	
	
	def __init__(self,host: str,porta: int|None,user: str,password: str,nomeDb: str,isDebug: bool):
		super().__init__()
		self.nomeDb=nomeDb
		if porta is None:
			porta=self.DEFAULT_PORT
		# apro la connessione col server
		self.connDb=mysql.connector.connect(user=user,password=password,host=host,port=porta,
				converter_class=MysqlCommonConverter)
		self.initCursor()
		self.TABLE_OPTIONS=self.getTableOptions(isDebug)
		self.isDbNew=None
	
	@abstractmethod
	def schema(self):
		"""
		Insert here sql instructions containing table definitions (DDL)
		"""
	
	def initDdl(self):
		#scelgo il db
		try:
			self.connDb.cmd_init_db(self.nomeDb)
			self.isDbNew=False
		except mysql.connector.ProgrammingError:
			sqlCreaDb="CREATE DATABASE %s;"%(self.nomeDb,)
			with self.initCursor() as cursoreDb:
				with self.lock:
					cursoreDb.execute(sqlCreaDb)
			self.connDb.cmd_init_db(self.nomeDb)
			self.isDbNew=True
		#se il db non esisteva creo le tabelle
		if self.isDbNew:
			sqlStr=ModuloStringhe.normalizzaEol(self.schema())
			for results in self.executeScript(sqlStr):
				yield results
	
	@staticmethod
	def getLastIdInserted(cursoreDb):
		return cursoreDb.lastrowid
	
	def selectNow(self):
		"""
		Returns current db date and time.
		"""
		sql="SELECT {};".format(self.DATE_TIME_NOW)
		with self.initCursor() as cursoreDb:
			with self.lock:
				cursoreDb.execute(sql,{})
			output=self.fetchOne(cursoreDb)
		return output
	
	def executeScript(self,sqlStr:str):
		sqlCmds=sqlStr.split(";")
		sqlCmds=ModuloListe.eliminaElementiVuoti(sqlCmds)
		numCmds=len(sqlCmds)
		cursoreDb=self.initCursor()
		for index,sqlCmd in enumerate(sqlCmds):
			sqlCmd=sqlCmd.strip()
			try:
				if sqlCmd!="":
					with self.lock:
						cursoreDb.execute(sqlCmd)
				yield index,numCmds
			except Exception as ex:
				raise ExceptionRuntime(sqlCmd+"\n\n"+ModuloLogging.exceptionToString(ex))
	
	def fetchAll(self,cursoreDb)->list:
		with cursoreDb:
			if cursoreDb.description is None:
				raise ExceptionDbNoData()
			descriptions=cursoreDb.description
			with self.lock:
				rows=cursoreDb.fetchall()
				self.commitNoLock()		# mysql mette in cache i risultati, lo risolvo così, è un bug loro...
		columns = [col[0] for col in descriptions]
		rows = [dict(zip(columns, row)) for row in rows]
		return rows
	
	@classmethod
	def backup(cls,percorsoCartella: str,user: str,password: str,dbName: str,
			ignoreTables:list|tuple|None)->list:
		output=[
			cls.backupDdl(percorsoCartella,user,password,dbName,ignoreTables),
			cls.backupData(percorsoCartella,user,password,dbName,ignoreTables)
		]
		return output
	
	@classmethod
	def backupDdl(cls,percorsoCartella: str,user: str,password: str,dbName: str,
			ignoreTables:list|tuple|None)->str:
		return cls.__backup(percorsoCartella,user,password,dbName,ignoreTables,True,False)
	@classmethod
	def backupData(cls,percorsoCartella: str,user: str,password: str,dbName: str,
			ignoreTables:list|tuple|None)->str:
		return cls.__backup(percorsoCartella,user,password,dbName,ignoreTables,False,True)
	
	@staticmethod
	def __backup(percorsoCartella:str,user:str,password:str,dbName:str,
			ignoreTables:list|tuple|None,onlyDdl:bool,onlyData:bool)->str:
		if onlyDdl and onlyData:
			raise ExceptionRuntime("valorizzare solo un'opzione alla volta")
		cmdIgnoreTables=""
		if ignoreTables is not None:
			cmdIgnoreTables=" ".join(["--ignore-table=%s.%s"%(dbName,x) for x in ignoreTables])
		nomefileSuffix=""
		cmdOptions=""
		if onlyDdl:
			nomefileSuffix="_ddl"
			cmdOptions="--no-data "+cmdIgnoreTables
		elif onlyData:
			nomefileSuffix="_data"
			cmdOptions="--order-by-primary --no-create-info --quick "+cmdIgnoreTables
		nomefileOutput=dbName+nomefileSuffix+".sql"
		percorsoFileBackup=ModuloFiles.pathJoin(percorsoCartella,nomefileOutput)
		cmd=r'mysqldump -u {} -p{} --databases {} --skip-add-drop-table --skip-comments {} -r "{}"'.format(user,password,dbName,cmdOptions,percorsoFileBackup)
		output=ModuloSystem.systemCallReturnOutput(cmd,None).strip()
		if not ModuloStringhe.isEmpty(output):
			raise ExceptionRuntime(output)
		return percorsoFileBackup
	
	@staticmethod
	def getTableOptions(isDebug: bool) -> str:
		return "ENGINE=%s DEFAULT CHARSET=utf8"%("InnoDB" if not isDebug else "MEMORY",)

def paginazione(firstResult:int,numResults:int)->str:
	sql=("LIMIT "+str(numResults) if numResults is not None else "")+\
			(" OFFSET "+str(firstResult) if firstResult is not None else "")
	return sql

def add_param_list(lista:list,prefix:str)->dict:
	params={}
	for index,elem in enumerate(lista):
		params[prefix+str(index)]=elem
	return params
