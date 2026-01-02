"""
esempio utilizzo per lista

def __query_NOME_TABELLA(self,lista_status,is_count):
	paramsStatus=ModuloSQLite.add_param_list(lista_status, "status")
	
	sql='''
SELECT '''+("COUNT(*)" if is_count is True else "*")+'''
FROM NOME_TABELLA
WHERE 1=1
AND status IN (:'''+",:".join(paramsStatus.keys())+''')
;
'''
	cursoreDb.execute(sql,paramsStatus)
"""
import sqlite3
from abc import abstractmethod

from modulitiz_nano.ModuloStringhe import ModuloStringhe
from modulitiz_micro.database.AbstractSql import AbstractSql
from modulitiz_nano.files.ModuloFiles import ModuloFiles


class AbstractSqlite(AbstractSql):
	"""
	select
	count
	insert
	update
	delete
	"""
	
	DATE_TIME_NOW="datetime('now','localtime')"
	DATE_TIME_NOW_MILLIS="strftime('%Y-%m-%d %H:%M:%f', 'now')"
	
	TIMEOUT_CONNECTION=10
	
	@abstractmethod
	def schema(self):
		"""
		Insert here sql instructions containing table definitions (DDL)
		"""
	
	def __init__(self,nomefile_db:str,show_sql:bool=False):
		super().__init__()
		self.isDbNew=ModuloFiles.getFileSize(nomefile_db)<=0
		#apro la connessione col db
		connDb=sqlite3.connect(nomefile_db, timeout=self.TIMEOUT_CONNECTION, detect_types=sqlite3.PARSE_DECLTYPES, check_same_thread=False)
		#modifica row factory per usare Row
		connDb.row_factory=sqlite3.Row
		self.connDb=connDb
		# creo il cursore, deve essere fatto dopo il row factory
		with self.initCursor() as cursoreDb:
			# setup iniziale
			with self.lock:
				# non puoi cancellare un record se e' referenziato da un'altra tabella
				cursoreDb.executescript('PRAGMA foreign_keys=ON;')
			self.commit()
			# mostra i comandi sql eseguiti
			if show_sql is True:
				self.connDb.set_trace_callback(print)
			# se il db non esisteva creo le tabelle
			if self.isDbNew:
				sql_str=ModuloStringhe.normalizzaEol(self.schema())
				with self.lock:
					cursoreDb.executescript(sql_str)
				self.commit()
	
	@staticmethod
	def getLastIdInserted(cursoreDb):
		return cursoreDb.lastrowid

def paginazione(first_result:int,num_results:int)->str:
	sql=("LIMIT "+str(num_results) if num_results is not None else "")
	sql+=(" OFFSET "+str(first_result) if first_result is not None else "")
	return sql

def add_param_list(lista,prefix):
	params={}
	for index,elem in enumerate(lista):
		params[prefix+str(index)]=elem
	return params
